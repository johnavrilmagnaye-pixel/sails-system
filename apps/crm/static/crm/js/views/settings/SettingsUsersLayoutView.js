Views.settings.SettingsUsersLayoutView = Vue.extend({
    template: '#settings-users-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin],
    components: {
        permissionsFormModal: Views.modals.PermissionsFormModalView
    },

    data: function () {
        return {
            currentUser: this.$root.currentUser,
            account: null,
            users: [],
            userRoles: [],
            onlyActive: false,
            modals: {
                permissionsForm: {
                    show: false,
                    data: {
                        user: null
                    }
                }
            }
        }
    },

    computed: {
        userRoles: function () {
            var userRoles = [
                {value: 'admin', text: i18n.gettext('Administrator')},
                {value: 'manager', text: i18n.gettext('Manager')}
            ];

            if (this.isOwner()) {
                userRoles.unshift({
                    value: 'owner', text: i18n.gettext('Account owner')
                })
            }

            return userRoles;
        }
    },

    route: {
        data: function (transition) {
            var self = this;

            return $.when(
                $.getJSON(API.users)
            ).then(function (usersData) {
                self.users = usersData;
            });
        }
    },

    ready: function () {
        var self = this;

        $(document).on('submit.modal', '.invite-user-modal form', function (e) {
            e.preventDefault();

            var $form = $(this),
                $modal = $form.closest('.modal'),
                $submit = $modal.find('button[type="submit"]');

            $submit.toggleBtnLoading(true);

            $.post(
                $form.attr('action'),
                $form.serializeArray()
            ).done(function (data) {
                $submit.toggleBtnLoading(false);

                if (data['success']) {
                    self.users = _.union(self.users, data.users);
                    $modal.modal('hide');
                    Utils.notify(i18n.gettext('Invitations sent.'));
                } else {
                    $modal.find('.modal-content').html(data);
                    init_modal_form($modal);
                }
            });
        });
    },

    beforeDestroy: function () {
        $(document).off('submit.modal', '.invite-user-modal form');
    },

    methods: {
        fetchUsers: function () {
            var self = this;

            $.getJSON(API.users).done(function (data) {
                self.users = data;
            });
        },
        changeUserStatus: function (user) {
            var postData = {
                status: user.is_active
            };

            $.post('/user/' + user.id + '/change_status/', postData).done(function (data) {
                if (!data.success) {
                    bootbox.dialog({
                        message: (
                            i18n.gettext('An error occurred. Please try again or contact support.')
                        ),
                        buttons: {
                            cansel: {
                                label: i18n.gettext('Close'),
                                className: 'btn-default'
                            }
                        }
                    });
                }
            });
        },
        changeUserRole: function (user) {
            if (user.role === 'owner') {
                this.makeOwner(user);
                return;
            }

            user.is_admin = user.role === 'admin';

            var postData = {
                role: user.role
            };

            $.post('/user/' + user.id + '/change_role/', postData);
        },
        makeOwner: function (user) {
            var self = this;

            bootbox.dialog({
                message: (
                    i18n.gettext('Are you sure you want to transfer account ownership to ') +
                    user.name + i18n.gettext('? You will retain administrator permissions.')
                ),
                buttons: {
                    cansel: {
                        label: i18n.gettext('Cancel'),
                        className: 'btn-default',
                        callback: function () {
                            self.fetchUsers();
                        }
                    },
                    danger: {
                        label: i18n.gettext('Make owner'),
                        className: 'btn-danger',
                        callback: function () {
                            $.post('/user/' + user.id + '/make_owner/').done(function (data) {
                                if (data['success']) {
                                    window.location.reload();
                                }
                            });
                        }
                    }
                }
            });
        },
        resendInvite: function (user) {
            var postData = {
                user_id: user.id
            };

            $.post(
                API.resendInvite,
                postData
            ).done(function (response) {
                Utils.notify(i18n.gettext('Invitation email to ') + user.email + i18n.gettext(' was sent successfully'), 'success');
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('An error occurred. Please try again or contact support.'), 'error');
            });
        },
        toggleOnlyActive: function (state) {
            if (this.onlyActive === state) {
                return;
            }

            this.onlyActive = state;
        },
        togglePermissionsFormModal: function (showModal, user) {
            this.modals.permissionsForm.data.user = user;
            this.modals.permissionsForm.show = showModal;
        },
    }
});
