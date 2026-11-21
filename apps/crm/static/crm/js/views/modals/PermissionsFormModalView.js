Views.modals.PermissionsFormModalView = Views.base.ModalView.extend({
    template: '#permissions-form-modal-tmpl',

    mixins: [Mixins.CommonMixin],

    props: ['modalData'],  // modalData: user
    data: function () {
        var data = this.modalData,
            perms = {
                add_company: this.hasPerm(data.user, 'add_company'),
                view_all_company: this.hasPerm(data.user, 'view_all_company'),
                change_own_company: this.hasPerm(data.user, 'change_own_company'),
                change_assigned_company: this.hasPerm(data.user, 'change_assigned_company'),
                change_all_company: this.hasPerm(data.user, 'change_all_company'),
                delete_own_company: this.hasPerm(data.user, 'delete_own_company'),

                add_person: this.hasPerm(data.user, 'add_person'),
                view_all_person: this.hasPerm(data.user, 'view_all_person'),
                change_own_person: this.hasPerm(data.user, 'change_own_person'),
                change_assigned_person: this.hasPerm(data.user, 'change_assigned_person'),
                change_all_person: this.hasPerm(data.user, 'change_all_person'),
                delete_own_person: this.hasPerm(data.user, 'delete_own_person'),

                add_deal: this.hasPerm(data.user, 'add_deal'),
                view_all_deal: this.hasPerm(data.user, 'view_all_deal'),
                change_own_deal: this.hasPerm(data.user, 'change_own_deal'),
                change_assigned_deal: this.hasPerm(data.user, 'change_assigned_deal'),
                change_all_deal: this.hasPerm(data.user, 'change_all_deal'),
                delete_own_deal: this.hasPerm(data.user, 'delete_own_deal'),

                add_task: this.hasPerm(data.user, 'add_task'),
                view_all_task: this.hasPerm(data.user, 'view_all_task'),
                change_own_task: this.hasPerm(data.user, 'change_own_task'),
                change_assigned_task: this.hasPerm(data.user, 'change_assigned_task'),
                delete_own_task: this.hasPerm(data.user, 'delete_own_task'),

                add_note: this.hasPerm(data.user, 'add_note'),
                view_all_note: this.hasPerm(data.user, 'view_all_note'),
                delete_own_note: this.hasPerm(data.user, 'delete_own_note'),

                add_upload: this.hasPerm(data.user, 'add_upload'),
                view_all_upload: this.hasPerm(data.user, 'view_all_upload'),
                delete_own_upload: this.hasPerm(data.user, 'delete_own_upload')
            };

        return {
            modalName: 'permissionsForm',
            user: data.user,
            perms: perms
        };
    },

    computed: {
        toggleAllText: function () {
            var isAllSelected = _.every(this.perms);

            return isAllSelected ? i18n.gettext('Remove'): i18n.gettext('Select');
        }
    },

    methods: {
        submit: function() {
            var self = this,
                $submit = $(this.$els.submit),
                postData = {
                    permissions: []
                };

            _.each(this.perms, function (value, key) {
                if (value) {
                    postData.permissions.push(key);
                }
            });

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.users + this.user.id + '/edit_permissions/',
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                self.user.permissions = response.user.permissions;
                Utils.notify(i18n.gettext('Permissions saved'));
                self.cancelModal();
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the changes. Please try again or contact support.')
                );
            });
        },

        hasPerm: function (user, perm) {
            return _.pluck(user.permissions, 'codename').indexOf(perm) > -1;
        },

        toggleAll: function () {
            var self = this,
                isAllSelected = _.every(this.perms),
                perms = {};

            _.each(this.perms, function (value, key) {
                 perms[key] = !isAllSelected;
            });

            this.perms = perms;
        }
    }
});
