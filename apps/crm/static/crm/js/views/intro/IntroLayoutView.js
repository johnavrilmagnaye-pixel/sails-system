Views.intro.IntroLayoutView = Vue.extend({
    template: '#intro-layout-tmpl',

    mixins: [Mixins.CommonMixin],
    components: {
        profileStep: Views.intro.IntroProfileStepView,
        usersStep: Views.intro.IntroUsersStepView,
        importStep1: Views.intro.IntroImportStep1View,
        importStep2: Views.intro.IntroImportStep2View
    },

    data: function () {
        return {
            intro: null,
            importStep: 1,
            introSteps: Const.INTRO_STEPS
        };
    },

    computed: {
        steps: function () {
            return [
                {
                    number: Const.INTRO_STEPS.ACCOUNT,
                    label: i18n.gettext('Create account'),
                    completed: true
                },
                {
                    number: Const.INTRO_STEPS.PROFILE,
                    label: i18n.gettext('Complete profile'),
                    completed: this.intro.current_step > Const.INTRO_STEPS.PROFILE
                },
                {
                    number: Const.INTRO_STEPS.USERS,
                    label: i18n.gettext('Invite users'),
                    completed: this.intro.current_step > Const.INTRO_STEPS.USERS
                },
                {
                    number: Const.INTRO_STEPS.IMPORT,
                    label: i18n.gettext('Import contacts'),
                    completed: false
                }
            ];
        }
    },

    route: {
        data: function (transition) {
            var self = this;

            return $.when(
                $.getJSON(API.intro),
                $.getJSON(API.users + 'current/')
            ).then(function (introData, currentUserData) {
                self.intro = introData[0];
                self.$root.currentUser = currentUserData[0];
            });
        }
    },

    ready: function () {
        $('.sidebar').toggleClass('hidden', true);
        $('.content').css({'padding-left': 0});
    },

    events: {
        profileStepCompleted: function () {
            this.intro.current_step = Const.INTRO_STEPS.USERS;
        },
        usersStepCompleted: function () {
            this.intro.current_step = Const.INTRO_STEPS.IMPORT;
        },
        importStep1Completed: function (data) {
            if (!data) {
                this.intro.is_completed = true;
                $('.sidebar').toggleClass('hidden', false);
                $('.content').css({'padding-left': '200px'});
                router.go(Urls.companies);
                return;
            }

            this.importStep = 2;
            this.importData = data;
        },
        importStep2Completed: function (contactsImportId) {
            this.contactsImportId = contactsImportId;
            setTimeout(this.checkContactsImport, 3000);
        },
        importStep2Canceled: function () {
            this.importStep = 1;
        }
    },

    methods: {
        checkContactsImport: function () {
            var self = this;

            $.getJSON(
                API.contactsImports + this.contactsImportId + '/'
            ).done(function (response) {
                if (response.is_completed) {
                    Utils.notify(response.msg || i18n.gettext('Contact import completed successfully'), 'success', 3000);
                    $('.sidebar').toggleClass('hidden', false);
                    $('.content').css({'padding-left': '200px'});
                    router.go(Urls.companies);
                    return;
                }

                setTimeout(self.checkContactsImport, 3000);
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Import error'), 'error');
            });
        }
    }
});
