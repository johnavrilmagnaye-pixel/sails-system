Vue.config.debug = false;
Vue.config.silent = true;

$(document).ajaxError(function (event, jqXHR, ajaxSettings, thrownError) {
    if (jqXHR && !ajaxSettings.suppressGlobalAuthRedirect) {
        switch (jqXHR.status) {
            case 403:
                // TODO show modal with session expired info
                window.location.replace(window.location.origin);
                break;
        }
    }
});

Storage.configure(CURRENT_ACCOUNT_ID);


// mobile toggle
$(document).on('click', '.toggle-sidebar', function () {
    $('.container-fluid').toggleClass('sidebar-active');
});

function toggleSidebar (isCollapsed, save) {
    $('.sidebar').toggleClass('sidebar-collapsed', isCollapsed);
    $('.content').toggleClass('content-expanded', isCollapsed);

    if (save) {
        Storage.saveCommon('isSidebarCollapsed', isCollapsed)
    }
}

var isSidebarCollapsed = !!Storage.fetchCommon('isSidebarCollapsed');
toggleSidebar(isSidebarCollapsed, false);
$('.sidebar').toggleClass('hidden', false);

var router = new VueRouter({
    history: true,
    suppressTransitionError: true
});


router.afterEach(function (transition) {
    var yaCounter = window.yaCounter33097483;

    if (yaCounter) {
        yaCounter.hit(transition.to.path, {
            referer: transition.from.path,
            params: {
                account: ACCOUNT
            }
        });
    }
});


var routes = {
    '/intro/': {
        component: Views.intro.IntroLayoutView
    },
    '/dashboard/': {
        component: Views.dashboard.DashboardLayoutView
    },
    '/notifications/': {
        component: Views.notifications.NotificationsLayoutView
    },

    '/companies/': {
	    component: Views.companies.CompanyListLayoutView
	},
	'/persons/': {
	    component: Views.persons.PersonListLayoutView
	},
    '/deals/': {
        component: Views.deals.DealListLayoutView
    },
    '/tasks/': {
        component: Views.tasks.TaskListLayoutView
    },

    '/companies/:id/': {
        component: Views.companies.CompanyCardLayoutView
    },
    '/persons/:id/': {
        component: Views.persons.PersonCardLayoutView
    },
    '/deals/:id/': {
        component: Views.deals.DealCardLayoutView
    },
    '/tasks/:id/': {
        component: Views.tasks.TaskCardLayoutView
    },

    '/settings/': {
        component: Views.settings.SettingsLayoutView,
        subRoutes: {
            'profile/': {
                component: Views.settings.SettingsProfileLayoutView
            },
            'users/': {
                component: Views.settings.SettingsUsersLayoutView
            },
            'company_fields/': {
                component: Views.settings.SettingsCompanyFieldsLayoutView
            },
            'person_fields/': {
                component: Views.settings.SettingsPersonFieldsLayoutView
            },
            'deal_fields/': {
                component: Views.settings.SettingsDealFieldsLayoutView
            },
            'task_fields/': {
                component: Views.settings.SettingsTaskFieldsLayoutView
            },
            'tags/': {
                component: Views.settings.SettingsTagsLayoutView
            },
            'contacts_imports/': {
                component: Views.settings.SettingsContactsImportLayoutView
            },
        }
    },

    // not found handler
    '*': {
        component: Views.companies.CompanyListLayoutView
    }
};

router.map(routes);

var App = Vue.extend({
    data: function () {
        return {
            i18n: i18n,
            currentAccount: {
                id: CURRENT_ACCOUNT_ID,
                name: CURRENT_ACCOUNT_NAME,
            },
            accounts: [{
                id: CURRENT_ACCOUNT_ID,
                name: CURRENT_ACCOUNT_NAME,
                is_selected: true
            }],
            selectedAccountId: CURRENT_ACCOUNT_ID,
            accountSwitching: false,
            sidebarCollapsed: isSidebarCollapsed,
            currentUser: {},
        }
    },

    created: function () {
        this.fetchCurrentAccount();
        this.fetchAccounts();
        this.fetchCurrentUser();
        this.watchAccountSwitches();
    },

    methods: {
        fetchCurrentAccount: function () {
            var self = this;

            $.getJSON(API.currentAccount).done(function (response) {
                self.currentAccount = response;
                self.selectedAccountId = response.id;
            });
        },
        fetchAccounts: function () {
            var self = this;

            $.getJSON(API.accounts).done(function (response) {
                self.accounts = response;
            });
        },
        switchAccount: function (accountId) {
            var self = this,
                previousAccountId = this.currentAccount.id;

            this.selectedAccountId = accountId;

            if (this.accountSwitching || this.selectedAccountId === previousAccountId) {
                return;
            }

            this.accountSwitching = true;
            $.ajax({
                url: API.switchAccount,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({account_id: this.selectedAccountId}),
                suppressGlobalAuthRedirect: true
            }).done(function (response) {
                localStorage.setItem('crm:account-switch', JSON.stringify({
                    accountId: response.id,
                    timestamp: new Date().getTime()
                }));
                window.location.reload();
            }).fail(function (response) {
                self.selectedAccountId = previousAccountId;
                self.accountSwitching = false;
                Utils.notify(
                    Utils.getResponseErrorMsg(response) ||
                        i18n.gettext('Could not switch account. Please try again.'),
                    'error'
                );
            });
        },
        toggleSidebar: function () {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            toggleSidebar(this.sidebarCollapsed, true);
        },
        watchAccountSwitches: function () {
            window.addEventListener('storage', function (event) {
                var accountSwitch;

                if (event.key !== 'crm:account-switch' || !event.newValue) {
                    return;
                }

                try {
                    accountSwitch = JSON.parse(event.newValue);
                } catch (error) {
                    return;
                }

                if (accountSwitch.accountId !== CURRENT_ACCOUNT_ID) {
                    window.location.reload();
                }
            });
        },
        fetchCurrentUser: function () {
            var self = this;

            $.getJSON(API.users + 'current/').done(function (response) {
                self.currentUser = response;
            });
        },
    },
});

router.start(App, '#app');
