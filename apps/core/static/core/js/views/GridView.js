Views.base.GridPaginationView = Vue.extend({
    template: '#grid-pagination-tmpl',
    replace: true,

    props: ['paginationData', 'itemsCnt', 'canChangePageSize'],
    data: function () {
        var res = {};

        if (this.canChangePageSize) {
            var pageSizeList = [10, 25, 50];

            if (this.$root.currentAccount.name === 'ormiss') {
                pageSizeList.push(100);
            }

            res.pageSizeList = pageSizeList;
        }

        return res;
    },

    computed: {
        start: function () {
            var data = this.paginationData;

            if (!data.count) {
                return 0;
            }

            return data.count > data.pageSize ? data.pageSize * (data.page - 1) + 1: data.page;
        },
        end: function () {
            if (!this.paginationData.count) {
                return 0;
            }

            return this.start + this.itemsCnt - 1;
        },
        lastPage: function () {
            return Math.ceil(this.paginationData.count / this.paginationData.pageSize);
        }
    },

    methods: {
        onPaginationClick: function (page) {
            if (page !== this.paginationData.page && page > 0 && page <= this.lastPage) {
                this.paginationData.page = page;
                // watcher in FetchDataMixin calls fetchData
            }
        },
        onPageSizeChange: function () {
            // watcher in FetchDataMixin calls fetchData
            Storage.save('pageSize', this.paginationData.pageSize);
        }
    }
});
