Views.persons.PersonListLayoutView = Vue.extend({
    template: '#person-list-layout-tmpl',

    mixins: [Mixins.CommonMixin],
    components: {
        grid: Views.persons.PersonGridView,
        filters: Views.persons.PersonFiltersFormView
    },

    data: function () {
        var filters = Storage.fetch('filters', {});

        return {
            filters: {
                show: Storage.fetch('showFilters', true),
                data: _.extend(filters, {
                    search: Storage.fetch('search', ''),
                })
            },
            personExtraFields: [],
            companyExtraFields: []
        }
    },

    route: {
        data: function (transition) {
            var self = this;

            return $.when(
                $.getJSON(API.extraFields)
            ).then(function (extraFieldsData) {
                self.personExtraFields = _.filter(extraFieldsData, {content_type: 'person'});
                self.companyExtraFields = _.filter(extraFieldsData, {content_type: 'company'});
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
