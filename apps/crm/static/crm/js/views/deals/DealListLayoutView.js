Views.deals.DealListLayoutView = Vue.extend({
    template: '#deal-list-layout-tmpl',

    mixins: [Mixins.CommonMixin],
    components: {
        grid: Views.deals.DealGridView,
        board: Views.deals.DealBoardView,
        funnel: Views.deals.DealFunnelView,
        filters: Views.deals.DealFiltersFormView
    },

    data: function () {
        var filters = Storage.fetch('filters', {});

        return {
            modelName: 'deal',
            itemsView: Storage.fetch('itemsView', 'grid'),
            filters: {
                show: Storage.fetch('showFilters', true),
                data: _.extend(filters, {
                    search: Storage.fetch('search', ''),
                    status: '1'
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
        toggleView: function (viewName) {
            this.itemsView = viewName;
            Storage.save('itemsView', viewName);
        },
        toggleFilters: function () {
            this.filters.show = !this.filters.show;
            Storage.save('showFilters', this.filters.show);
        },
        refresh: function () {
            this.$refs.itemsView.fetchData(true);
        }
    }
});
