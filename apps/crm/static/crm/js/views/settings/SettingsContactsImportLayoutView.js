Views.settings.SettingsContactsImportLayoutView = Vue.extend({
    template: '#settings-contacts-import-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin],
    components: {
        gridPagination: Views.base.GridPaginationView,
        tagsModal: Views.modals.TagsModalView,
        responsiblesModal: Views.modals.ResponsiblesModalView
    },

    data: function () {
        return {
            itemsApiUrl: API.contactsImports,
            items: [],
            paginationData: {
                page: 1,
                pageSize: 25,
                count: null,
                previous: null,
                next: null
            },
            modals: {
                responsibles: {
                    show: false,
                    data: {
                        baseUrl: null,
                        targetLabel: i18n.gettext('imported contacts'),
                        isGrid: false
                    }
                },
                tags: {
                    show: false,
                    data: {
                        baseUrl: null,
                        targetLabel: i18n.gettext('imported contacts'),
                        isGrid: false
                    }
                }
            }
        }
    },

    route: {
        data: function (transition) {
            var self = this,
                queryParams = this.getFetchDataParams();

            return $.getJSON(this.itemsApiUrl, queryParams).done(function (contactImports) {
                self.setFetchDataResponse(contactImports);
            });
        }
    },

    methods: {
        getFetchDataParams: function () {
            return {
                page: this.paginationData.page,
                page_size: this.paginationData.pageSize
            };
        },
        getBaseUrl: function(contactsImportId) {
            return API.contactsImports + contactsImportId + '/';
        },
        toggleResponsiblesModal: function (showModal, contactsImportId) {
            this.modals.responsibles.show = showModal;
            if (contactsImportId) {
                this.modals.responsibles.data.baseUrl = this.getBaseUrl(contactsImportId);
            }
        },
        toggleTagsModal: function (showModal, contactsImportId) {
            this.modals.tags.show = showModal;
            if (contactsImportId) {
                this.modals.tags.data.baseUrl = this.getBaseUrl(contactsImportId);
            }
        }

    }
});
