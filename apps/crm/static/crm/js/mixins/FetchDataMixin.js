Mixins.FetchDataMixin = {
    methods: {
        getFetchDataParams: function (resetPage) {
            if (!!this.paginationData) {
                this.paginationData.page = resetPage ? 1 : this.paginationData.page;
            } else {
                this.page = resetPage ? 1 : this.page;
            }

            var queryParams = {
                sorting: this.sortOrder + this.sortField
            };

            if (!!this.paginationData) {
                queryParams.page = this.paginationData.page;
                queryParams.page_size = this.paginationData.pageSize;
            } else {
                queryParams.page = this.page;
                queryParams.page_size = this.pageSize;
            }

            return _.merge(queryParams, _.pick(this.filters, _.identity));
        },
        setFetchDataResponse: function (data) {
            if (_.isEmpty(data)) {
                this.items = [];
                return;
            }

            this.items = data.results;
            this.checkedAll = false;

            if (!!this.paginationData) {
                this.paginationData.count = data.count;
                this.paginationData.previous = data.previous;
                this.paginationData.next = data.next;
            } else {
                this.count = data.count;
                this.previous = data.previous;
                this.next = data.next;
            }
        },
        fetchData: function (resetPage) {
            var self = this,
                queryParams = this.getFetchDataParams(resetPage);

            $.getJSON(this.itemsApiUrl, queryParams).done(function (data) {
                self.setFetchDataResponse(data)
            });
        }
    },
    watch: {
        filters: {
            deep: true,
            handler: function () {
                if (!this._isReady) {
                    return;
                }

                this.fetchData(true);
            }
        },
        'paginationData.pageSize': {
            handler: function () {
                if (!this._isReady) {
                    return;
                }

                this.fetchData(true);
            }
        },
        'paginationData.page': {
            handler: function () {
                if (!this._isReady) {
                    return;
                }

                this.fetchData(false);
            }
        }
    }
};
