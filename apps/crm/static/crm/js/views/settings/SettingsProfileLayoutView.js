Views.settings.EditProfileForm = Vue.extend({
    template: '#edit-profile-form-tmpl',
    replace: true,

    data: function () {
        var currentUser = this.$root.currentUser;

        return {
            form: {
                email: {
                    value: currentUser.email,
                    error: ''
                },
                first_name: {
                    value: currentUser.first_name,
                    error: ''
                },
                last_name: {
                    value: currentUser.last_name,
                    error: ''
                },
                timezone: {
                    value: currentUser.timezone,
                    error: ''
                },
                language: {
                    value: currentUser.language,
                    error: ''
                }
            },
            timezones: Const.TIMEZONES,
            languages: Const.LANGUAGES
        }
    },

    methods: {
        onSubmit: function (e) {
            var self = this,
                postData = {
                    email: this.form.email.value,
                    first_name: this.form.first_name.value,
                    last_name: this.form.last_name.value,
                    timezone: this.form.timezone.value,
                    language: this.form.language.value
                },
                $form = $(e.currentTarget),
                $submit = $form.find('button[type="submit"]');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.editProfile,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);

                _.forOwn(self.form, function (value, key) {
                    self.form[key].error = '';
                });
                self.$root.currentUser = response;
                Utils.notify(i18n.gettext('Profile saved'));
                if (response.language !== i18n.locale) {
                    window.location.reload();
                }
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);

                var errors;

                if (response.responseJSON.errors) {
                    errors = response.responseJSON.errors;

                    _.forOwn(self.form, function (value, key) {
                        self.form[key].error = !!errors[key] ? errors[key] : '';
                    });
                }
            });
        }
    }
});


Views.settings.ChangePasswordForm = Vue.extend({
    template: '#change-password-form-tmpl',
    replace: true,

    data: function () {
        return {
            form: {
                current_password: {
                    value: '',
                    error: ''
                },
                new_password: {
                    value: '',
                    error: ''
                }
            }
        }
    },

    methods: {
        onSubmit: function (e) {
            if (!this.form.current_password.value) {
                Utils.notify(i18n.gettext('Current password is required'), 'error');
                return;
            }

            if (!this.form.new_password.value) {
                Utils.notify(i18n.gettext('New password is required'), 'error');
                return;
            }

            var self = this,
                postData = {
                    current_password: this.form.current_password.value,
                    new_password: this.form.new_password.value
                },
                $form = $(e.currentTarget),
                $submit = $form.find('button[type="submit"]');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.changePassword,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);

                _.forOwn(self.form, function (value, key) {
                    self.form[key].value = '';
                    self.form[key].error = '';
                });
                Utils.notify(i18n.gettext('Password changed'));
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);

                var errors;

                if (response.responseJSON.errors) {
                    errors = response.responseJSON.errors;

                    _.forOwn(self.form, function (value, key) {
                        self.form[key].error = !!errors[key] ? errors[key] : '';
                    });
                }
            });
        }
    }
});


Views.settings.NotificationSettingsForm = Vue.extend({
    template: '#notification-settings-form-tmpl',
    replace: true,

    props: ['notificationSettings'],
    data: function () {
        return {
            form: {
                remind_task: {
                    value: this.notificationSettings.remind_task,
                    error: ''
                },
                remind_task_before_hours: {
                    value: this.notificationSettings.remind_task_before_hours,
                    error: ''
                },
                remind_task_before_minutes: {
                    value: this.notificationSettings.remind_task_before_minutes,
                    error: ''
                },
                notify_task_completed: {
                    value: this.notificationSettings.notify_task_completed,
                    error: ''
                },
                notify_company_note: {
                    value: this.notificationSettings.notify_company_note,
                    error: ''
                },
                notify_person_note: {
                    value: this.notificationSettings.notify_person_note,
                    error: ''
                },
                notify_deal_note: {
                    value: this.notificationSettings.notify_deal_note,
                    error: ''
                },
                notify_task_note: {
                    value: this.notificationSettings.notify_task_note,
                    error: ''
                },
                notify_company_responsibles: {
                    value: this.notificationSettings.notify_company_responsibles,
                    error: ''
                },
                notify_person_responsibles: {
                    value: this.notificationSettings.notify_person_responsibles,
                    error: ''
                },
                notify_deal_responsibles: {
                    value: this.notificationSettings.notify_deal_responsibles,
                    error: ''
                },
                notify_task_responsibles: {
                    value: this.notificationSettings.notify_task_responsibles,
                    error: ''
                }
            }
        }
    },

    methods: {
        onSubmit: function (e) {
            var self = this,
                postData = {
                    remind_task: this.form.remind_task.value,
                    remind_task_before_hours: this.form.remind_task_before_hours.value,
                    remind_task_before_minutes: this.form.remind_task_before_minutes.value,
                    notify_task_completed: this.form.notify_task_completed.value,
                    notify_company_note: this.form.notify_company_note.value,
                    notify_person_note: this.form.notify_person_note.value,
                    notify_deal_note: this.form.notify_deal_note.value,
                    notify_task_note: this.form.notify_task_note.value,
                    notify_item_responsibles: {
                        company: this.form.notify_company_responsibles.value,
                        person: this.form.notify_person_responsibles.value,
                        deal: this.form.notify_deal_responsibles.value,
                        task: this.form.notify_task_responsibles.value
                    }
                },
                $form = $(e.currentTarget),
                $submit = $form.find('button[type="submit"]');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.editNotificationSettings,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);

                _.forOwn(self.form, function (value, key) {
                    self.form[key].error = '';
                });
                Utils.notify(i18n.gettext('Notification settings saved'));
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);

                var errors;

                if (response.responseJSON.errors) {
                    errors = response.responseJSON.errors;

                    _.forOwn(self.form, function (value, key) {
                        self.form[key].error = !!errors[key] ? errors[key] : '';
                    });
                }
            });
        }
    }
});


Views.settings.SettingsProfileLayoutView = Vue.extend({
    template: '#settings-profile-layout-tmpl',

    mixins: [Mixins.CommonMixin],
    components: {
        editProfileForm: Views.settings.EditProfileForm,
        changePasswordForm: Views.settings.ChangePasswordForm,
        notificationSettingsForm: Views.settings.NotificationSettingsForm
    },

    data: function () {
        return {
            notificationSettings: {}
        };
    },

    ready: function () {
        var self = this;

        $(document).on('change.settings-profile-account', '.account-switcher select[name="account"]', function () {
            var accountId = $(this).val();

            if (String(accountId) !== String(self.$root.currentAccount.id)) {
                self.$root.switchAccount(accountId);
            }
        });
    },

    beforeDestroy: function () {
        $(document).off('.settings-profile-account');
    },

    route: {
        data: function (transition) {
            var self = this;

            return $.when(
                $.getJSON(API.users + 'current/'),
                $.getJSON(API.notificationSettings)
            ).then(function (userData, notificationSettingsData) {
                self.$root.currentUser = userData[0];
                self.notificationSettings = notificationSettingsData[0];
            });
        }
    }
});
