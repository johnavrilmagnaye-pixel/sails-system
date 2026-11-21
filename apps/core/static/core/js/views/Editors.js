(function() {

    Views.base.Editor = Vue.extend({
        replace: true,

        props: ['fieldData'],
        data: function () {
            return this.fieldData;
        }
    });


    Views.editors.TextEditor = Views.base.Editor.extend({
        template: '#text-editor-tmpl'
    });


    Views.editors.TextAreaEditor = Views.base.Editor.extend({
        template: '#text-area-editor-tmpl'
    });


    Views.editors.SelectEditor = Views.base.Editor.extend({
        template: '#select-editor-tmpl'
    });


    Views.editors.DateEditor = Views.base.Editor.extend({
        template: '#date-editor-tmpl'
    });


    Views.editors.DateTimeEditor = Views.base.Editor.extend({
        template: '#date-time-editor-tmpl'
    });


    Views.editors.TimeEditor = Views.base.Editor.extend({
        template: '#time-editor-tmpl'
    });


    Views.editors.DateRangeEditor = Views.base.Editor.extend({
        template: '#date-range-editor-tmpl'
    });


    Views.editors.NumberRangeEditor = Views.base.Editor.extend({
        template: '#number-range-editor-tmpl'
    });


    Views.editors.ListEditor = Views.base.Editor.extend({
        template: '#list-editor-tmpl',

        data: function () {
            var data = this.fieldData;

            data.addMoreText = data.addMoreText || i18n.gettext('Add another');

            return data;
        },

        computed: {
            showAddMore: function () {
                return !(
                    (this.maxItems && this.maxItems >= this.items.length) ||
                    (!this.alwaysShowAddMore && this.items.length === 1 && !this.items[0].value)
                )
            }
        },

        methods: {
            addItem: function () {
                var lastIndex = _.max(_.pluck(this.items, 'id'));

                this.items.push({
                    id: lastIndex + 1,
                    value: ''
                });
            },

            removeItem: function (item) {
                this.items.$remove(item);
            },

            updateValue: function () {
                this.value = _.without(_.pluck(this.items, 'value'), '');
            }
        },

        watch: {
            items: {
                deep: true,
                handler: function () {
                    _.debounce(this.updateValue, 500)();
                }
            }
        }
    });

    Views.editors.DropzoneEditor = Views.base.Editor.extend({
        template: '#dropzone-editor-tmpl'
    });

    Views.editors.PhoneListEditor = Views.editors.ListEditor.extend({
        template: '#phone-list-editor-tmpl'
    });

})();
