Views.common.CardExtraFieldsView = Vue.extend({
    template: '#card-extra-fields-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin],

    props: ['extraFields', 'item'],
    data: function () {
        return {
            extraFieldTypes: Const.EXTRA_FIELD_TYPES
        }
    },

    methods: {

    }
});
