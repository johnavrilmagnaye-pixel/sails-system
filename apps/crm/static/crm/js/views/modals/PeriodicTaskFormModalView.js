Views.modals.PeriodicTaskFormModalView = Views.base.ModalView.extend({
    template: '#periodic-task-form-modal-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        textAreaEditor: Views.editors.TextAreaEditor,
        selectEditor: Views.editors.SelectEditor,
        dateEditor: Views.editors.DateEditor,
        dateTimeEditor: Views.editors.DateTimeEditor,
        timeEditor: Views.editors.TimeEditor,
        dropzoneEditor: Views.editors.DropzoneEditor
    },

    props: ['modalData'], // extraFields, instance
    data: function () {
        var data = this.modalData;

        data.modalName = 'periodicTaskForm';

        var form = {
            name: {
                name: 'name',
                label: i18n.gettext('Name'),
                editor: 'text-editor',
                value: '',
                error: ''
            },
            company: {
                name: 'company',
                label: i18n.gettext('Company'),
                placeholder: i18n.gettext('Select a company'),
                editor: 'select-editor',
                optionType: 'company',
                options: !!data.initialCompany ? [{id: data.initialCompany.id, text: data.initialCompany.name}] : [],
                allowClear: true,
                minInput: 2,
                value: !!data.initialCompany ? data.initialCompany.id : '',
                error: ''
            },
            person: {
                name: 'person',
                label: i18n.gettext('Person'),
                placeholder: i18n.gettext('Select a contact'),
                editor: 'select-editor',
                optionType: 'person',
                options: !!data.initialPerson ? [{id: data.initialPerson.id, text: data.initialPerson.name}] : [],
                queryParams: {},
                allowClear: true,
                minInput: 2,
                value: !!data.initialPerson ? data.initialPerson.id : '',
                error: ''
            },
            deal: {
                name: 'deal',
                label: i18n.gettext('Deal'),
                placeholder: i18n.gettext('Select a deal'),
                editor: 'select-editor',
                optionType: 'deal',
                options: !!data.initialDeal ? [{id: data.initialDeal.id, text: data.initialDeal.name}] : [],
                queryParams: {},
                allowClear: true,
                value: !!data.initialDeal ? data.initialDeal.id : '',
                error: ''
            },
            time: {
                name: 'time',
                label: i18n.gettext('Time'),
                editor: 'time-editor',
                value: '',
                error: '',
                hidden: true
            },
            period: {
                name: 'period',
                label: i18n.gettext('Repeat'),
                editor: 'select-editor',
                options: [
                    {id: 3, text: i18n.gettext('Every week')},
                    {id: 4, text: i18n.gettext('By month')}
                ],
                value: 3,
                error: '',
                hidden: true
            },
            weekdays: {
                name: 'weekdays',
                label: i18n.gettext('Weekday'),
                editor: 'select-editor',
                options: [
                    {id: 0, text: i18n.gettext('Every day')},
                    {id: 1, text: i18n.gettext('Monday')},
                    {id: 2, text: i18n.gettext('Tuesday')},
                    {id: 3, text: i18n.gettext('Wednesday')},
                    {id: 4, text: i18n.gettext('Thursday')},
                    {id: 5, text: i18n.gettext('Friday')},
                    {id: 6, text: i18n.gettext('Saturday')},
                    {id: 7, text: i18n.gettext('Sunday')}
                ],
                multiple: true,
                placeholder: i18n.gettext('Select weekdays'),
                value: '',
                error: '',
                hidden: true
            },
            months: {
                name: 'months',
                label: i18n.gettext('Months'),
                editor: 'select-editor',
                options: [
                    {id: 0, text: i18n.gettext('Every month')},
                    {id: 1, text: i18n.gettext('January')},
                    {id: 2, text: i18n.gettext('February')},
                    {id: 3, text: i18n.gettext('March')},
                    {id: 4, text: i18n.gettext('April')},
                    {id: 5, text: i18n.gettext('May')},
                    {id: 6, text: i18n.gettext('June')},
                    {id: 7, text: i18n.gettext('July')},
                    {id: 8, text: i18n.gettext('August')},
                    {id: 9, text: i18n.gettext('September')},
                    {id: 10, text: i18n.gettext('October')},
                    {id: 11, text: i18n.gettext('November')},
                    {id: 12, text: i18n.gettext('December')}
                ],
                multiple: true,
                placeholder: i18n.gettext('Select months'),
                value: '',
                error: '',
                hidden: true
            },
            monthdays: {
                name: 'monthdays',
                label: i18n.gettext('Number'),
                editor: 'select-editor',
                options: _.map(_.range(1, 32), function (number) {
                    return {id: number, text: number};
                }),
                multiple: true,
                placeholder: i18n.gettext('Select days of month'),
                value: '',
                error: '',
                hidden: true
            }
        };

        // this.initExtraFields(form, data.extraFields);

        form = _.extend(form, {
            tags: {
                name: 'tags',
                label: i18n.gettext('Tags'),
                placeholder: i18n.gettext('Select tags'),
                editor: 'select-editor',
                optionType: 'tag',
                multiple: true,
                tags: true,
                value: '',
                error: ''
            },
            responsibles: {
                name: 'responsibles',
                label: i18n.gettext('Assignees'),
                placeholder: i18n.gettext('Select assignees'),
                editor: 'select-editor',
                multiple: true,
                optionType: 'user',
                value: '',
                error: ''
            },
            details: {
                name: 'details',
                label: i18n.gettext('Task description'),
                editor: 'text-area-editor',
                cols: 40,
                rows: 10,
                value: '',
                error: ''
            }
        });
        
        data.isEdit = false;
        if (!!data.instance) {
            data.isEdit = true;
            this.setInstanceValues(form, data.instance);
        }

        data.form = form;

        return data;
    },

    ready: function () {
        this.$watch('form.company.value', function (value) {
            if (!!this.form.person) {
                this.form.person.queryParams.company = value;

                if (!value) {
                    this.form.person.value = '';
                }
            }

            if (!!this.form.deal) {
                this.form.deal.queryParams.company = value;

                if (!value) {
                    this.form.deal.value = '';
                }
            }
        });

        this.$watch('form.person.value', function (value) {
            this.form.deal.queryParams.person = value;

            if (!value) {
                this.form.deal.value = '';
            }
        });
    },

    methods: {
        submit: function () {
            var self = this,
                $submit = $(this.$els.submit),
                formData = this.getFormData(),
                url = API.periodicTasks + (!!self.instance ? self.instance.id + '/edit/' : 'add/');

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: url,
                type: 'POST',
                data: JSON.stringify(formData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);
                Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New recurring task added'));
                self.$dispatch('periodicTaskSaved');
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                self.handleFormErrors(
                    response,
                    i18n.gettext('Could not save the task. Please try again or contact support.')
                );
            });
        }
    }
});
