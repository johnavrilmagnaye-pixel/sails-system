Views.dashboard.DashboardLayoutView = Vue.extend({
    template: '#dashboard-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin],
    components: {
        gridPagination: Views.GridPaginationView
    },

    data: function () {
        return {
            stats: {},
            activity: [],
            paginationData: {
                page: 1,
                pageSize: 50,
                count: null,
                previous: null,
                next: null
            },
            filters: {
                created_at: moment().subtract(29, 'days').format('DD.MM.YYYY') + ' - ' + moment().format('DD.MM.YYYY'),
                user: '',
                content_type: ''
            },
            maxDate: moment(),
            contentTypes: [
                {id: 'company', text: i18n.gettext('Companies')},
                {id: 'person', text: i18n.gettext('Persons')},
                {id: 'task', text: i18n.gettext('Tasks')},
                {id: 'deal', text: i18n.gettext('Deals')},
                {id: 'note', text: i18n.gettext('Notes')},
                {id: 'upload', text: i18n.gettext('Files')}
            ]
        }
    },

    methods: {
        getFetchDataParams: function (resetPage) {
            var queryParams = {
                page_size: this.paginationData.pageSize,
                page: resetPage ? 1 : this.paginationData.page
            };

            return _.merge(queryParams, _.pick(this.filters, _.identity));
        },
        fetchData: function (resetPage) {
            var self = this,
                queryParams = this.getFetchDataParams(resetPage);

            $.getJSON(API.dashboardStats, {created_at: self.filters.created_at}).done(function (response) {
                self.stats = response.stats_data;
            });

            $.getJSON(API.dashboardActivity, queryParams).done(function (response) {
                self.activity = response.results;
                self.paginationData.count = response.count;
                self.paginationData.previous = response.previous;
                self.paginationData.next = response.next;
            });
        }
    }
});
