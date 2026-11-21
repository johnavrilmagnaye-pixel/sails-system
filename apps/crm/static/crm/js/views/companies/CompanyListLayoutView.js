Views.companies.CompanyListLayoutView = Vue.extend({
    template: '#company-list-layout-tmpl',

    mixins: [Mixins.CommonMixin],
    components: {
        grid: Views.companies.CompanyGridView,
        filters: Views.companies.CompanyFiltersFormView
    },

    data: function () {
        var filters = Storage.fetch('filters', {});

        return {
            modelName: 'company',
            filters: {
                show: Storage.fetch('showFilters', true),
                data: _.extend(filters, {
                    search: Storage.fetch('search', ''),
                })
            },
            extraFields: []
        }
    },

    route: {
        data: function (transition) {
            var self = this;

            return $.when(
                $.getJSON(API.extraFields, {content_type__model: this.modelName})
            ).then(function (extraFieldsData) {
                self.extraFields = extraFieldsData;
            });
        }
    },

    ready: function () {
        var self = this;

        this.$watch('filters.data.search', function () {
            Storage.save('search', self.filters.data.search);
        });
    },

    methods: {
        toggleFilters: function () {
            this.filters.show = !this.filters.show;
            Storage.save('showFilters', this.filters.show);
        },
        refresh: function () {
            this.$refs.itemsView.fetchData(true);
        }
    }
});
