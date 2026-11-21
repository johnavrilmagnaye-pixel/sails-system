Views.base.UiState = Vue.extend({
    template: '#ui-state-tmpl',
    props: {
        kind: {
            type: String,
            default: 'empty'
        },
        message: {
            type: String,
            required: true
        }
    }
});

Vue.component('ui-state', Views.base.UiState);
