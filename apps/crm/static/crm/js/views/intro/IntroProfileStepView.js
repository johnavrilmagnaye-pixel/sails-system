Views.intro.IntroProfileStepView = Vue.extend({
    template: '#intro-profile-step-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        selectEditor: Views.editors.SelectEditor
    },

    data: function () {
        var data = {};

        var form = {
            email: {
                name: 'email',
                label: i18n.gettext('Email address'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            first_name: {
                name: 'first_name',
                label: i18n.gettext('First name'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            last_name: {
                name: 'last_name',
                label: i18n.gettext('Last name'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            timezone: {
                name: 'timezone',
                label: i18n.gettext('Time zone'),
                editor: 'select-editor',
                options: Const.TIMEZONES,
                value: 'Europe/Moscow',
                error: ''
            },
            language: {
                name: 'language',
                label: i18n.gettext('Interface language'),
                editor: 'select-editor',
                options: Const.LANGUAGES,
                value: 'en',
                error: ''
            }
        };

        data.form = form;

        return data;
    },

    ready: function () {
        this.form.email.value = this.$root.currentUser.email;
        this.form.first_name.value = this.$root.currentUser.first_name;
        this.form.last_name.value = this.$root.currentUser.last_name;
        this.form.timezone.value = this.$root.currentUser.timezone;
        this.form.language.value = this.$root.currentUser.language;
    },

    methods: {
        onSubmit: function () {
            var self = this,
                $submit = $(this.$els.submit),
                postData = this.getFormData();

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: API.editProfile,
                type: 'POST',
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(i18n.gettext('Profile saved'));
                if (response.language !== i18n.locale) {
                    window.location.reload();
                } else {
                    self.$dispatch('profileStepCompleted');
                }
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the task. Please try again or contact support.')
                );
            });
        }
    }
});
