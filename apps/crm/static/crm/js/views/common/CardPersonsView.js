Views.common.CardPersonsView = Vue.extend({
    template: '#card-persons-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin],

    props: ['persons']
});
