Views.tasks.TaskListLayoutView = Vue.extend({
    template: '#task-list-layout-tmpl',

    mixins: [Mixins.CommonMixin],
    components: {
        grid: Views.tasks.TaskGridView,
        calendar: Views.tasks.TaskCalendarView,
        periodic: Views.tasks.PeriodicTasksView,
        filters: Views.tasks.TaskFiltersFormView
    },

    data: function () {
        var filters = Storage.fetch('filters', {}),
            itemsView = Storage.fetch('itemsView', 'grid');

        return {
            modelName: 'task',
            itemsView: itemsView,
            filters: {
                show: itemsView !== 'periodic' ? Storage.fetch('showFilters', true) : false,
                data: _.extend(filters, {
                    search: Storage.fetch('search', ''),
                    state: '1'
                })
            },
            extraFields: [],
            showFilterToggle: itemsView !== 'periodic'
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

            this.filters.show = this.itemsView !== 'periodic';
            this.showFilterToggle = this.itemsView !== 'periodic';
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
