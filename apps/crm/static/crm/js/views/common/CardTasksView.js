Views.common.CardTasksView = Vue.extend({
    template: '#card-tasks-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin],

    props: ['tasks']
});
