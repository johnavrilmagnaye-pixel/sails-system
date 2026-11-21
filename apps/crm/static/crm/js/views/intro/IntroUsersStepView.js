Views.intro.IntroUsersStepView = Vue.extend({
    template: '#intro-users-step-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor
    },

    data: function () {
        var data = {};

        var form = {
            email_1: {
                name: 'email_1',
                label: i18n.gettext('Email address'),
                editor: 'text-editor',
                inputType: 'email',
                value: '',
                error: ''
            },
            email_2: {
                name: 'email_2',
                label: i18n.gettext('Email address'),
                editor: 'text-editor',
                inputType: 'email',
                value: '',
                error: ''
            },
            email_3: {
                name: 'email_3',
                label: i18n.gettext('Email address'),
                editor: 'text-editor',
                inputType: 'email',
                value: '',
                error: ''
            }
        };

        data.form = form;

        return data;
    },

    computed: {
        showMoreLink: function () {
            return _.keys(this.form).length < 9;
        }
    },

    methods: {
        addMore: function (e) {
            var fieldName = 'email_' + (_.keys(this.form).length + 1);

            Vue.set(this.form, fieldName, {
                name: fieldName,
                label: i18n.gettext('Email address'),
                editor: 'text-editor',
                inputType: 'email',
                value: '',
                error: ''
            });
        },
        onSkip: function (e) {
            var self = this,
                $submit = $(this.$els.submit);

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.intro + 'skip_step/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                self.$dispatch('usersStepCompleted');
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('An error occurred. Please try again or contact support.')
                );
            });
        },
        onSubmit: function (e) {
            var self = this,
                $submit = $(this.$els.submit),
                postData = {
                    emails: _.compact(_.values(this.getFormData()))
                };

            if (_.isEmpty(postData.emails)) {
                Utils.notify(i18n.gettext('Enter at least one email address'), 'error');
                return;
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.intro + 'invite_users/',
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('User invitations sent'));
                self.$dispatch('usersStepCompleted');
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not send invitations. Please try again or contact support.')
                );
            });
        }
    }
});
