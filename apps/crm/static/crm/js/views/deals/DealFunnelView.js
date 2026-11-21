Views.deals.DealFunnelView = Vue.extend({
    template: '#deal-funnel-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin, Mixins.FetchDataMixin],

    props: ['filters'],
    data: function () {
        return {
            itemsApiUrl: API.dealsFunnel,
            modelName: 'deal',
            modelPlural: i18n.gettext('deal'),
            chartData: {},
            tableData: {
                stages: [],
                currencies: [],
                totalBudgets: [],
                totalConversion: 0
            },
            chart: null
        }
    },

    activate: function (done) {
        var self = this,
            itemsParams = this.getFetchDataParams();

        $.when(
            $.getJSON(this.itemsApiUrl, itemsParams)
        ).then(function (itemsData) {
            self.setFetchDataResponse(itemsData);
            done();
        });
    },

    beforeDestroy: function () {
        if (this.chart) {
            this.chart.destroy();
        }
    },

    methods: {
        getFetchDataParams: function () {
            return _.pick(this.filters, _.identity);
        },
        setFetchDataResponse: function (data) {
            this.chartData = data.chart_data;
            this.tableData = data.table_data;
        },
        initChart: function () {
            var $chartWrapper = $(this.$els.chartWrapper),
                ctx;

            $chartWrapper.html('<canvas id="funnel-chart" width="800" height="400"></canvas>');
            ctx = $chartWrapper.find('canvas').get(0).getContext("2d");

            this.chart = new Chart(ctx, {
                type: 'bar',
                data: this.chartData,
                options: {
                    barValueSpacing: 10,
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: false
                    },
                    tooltips: {
                        callbacks: {
                            title: function (tooltipItem, data) {
                                return data.labels[tooltipItem[0].index];
                            },
                            label: function (tooltipItem, data) {
                                return tooltipItem.yLabel + ' ' + Utils.pluralize(
                                    tooltipItem.yLabel,
                                    i18n.gettext('deal'), i18n.gettext('deals')
                                );
                            }
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                callback: function (value) {
                                    return value % 1 === 0 ? value.toString() : '';
                                }
                            }
                        }],
                        xAxes: [{
                            ticks: {
                                maxRotation: 30,
                                callback: function (value) {
                                    return value.length > 15 ? value.substr(0, 12) + '...' : value;
                                }
                            }
                        }]
                    }
                }
            });
        }
    },
    watch: {
        chartData: {
            deep: true,
            handler: function (value) {
                if (!_.isEmpty(value)) {
                    if (this.chart) {
                        //for (var i = 0; i < value.datasets[0].data.length; i++) {
                        //    this.chart.datasets[0].bars[i].value = value.datasets[0].data[i];
                        //}
                        this.chart.data.datasets[0].data = value.datasets[0].data;
                        this.chart.update();
                    } else {
                        this.initChart();
                    }
                }
            }
        }
    }
});
