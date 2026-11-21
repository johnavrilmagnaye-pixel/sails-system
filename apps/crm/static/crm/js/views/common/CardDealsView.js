Views.common.CardDealsView = Vue.extend({
    template: '#card-deals-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin],

    props: ['deals']
});
