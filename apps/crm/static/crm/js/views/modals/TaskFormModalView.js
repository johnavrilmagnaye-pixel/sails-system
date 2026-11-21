Views.modals.TaskFormModalView = Views.base.ModalView.extend({
    template: '#task-form-modal-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FormMixin],
    components: {
        textEditor: Views.editors.TextEditor,
        textAreaEditor: Views.editors.TextAreaEditor,
        selectEditor: Views.editors.SelectEditor,
        dateEditor: Views.editors.DateEditor,
        dateTimeEditor: Views.editors.DateTimeEditor,
        dropzoneEditor: Views.editors.DropzoneEditor
    },

    props: ['modalData'], // extraFields, instance, initialCompany, initialPerson, initialDeal
    data: function () {
        var data = this.modalData;

        data.modalName = 'taskForm';

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
            expire_date: {
                name: 'expire_date',
                label: i18n.gettext('Due date'),
                editor: 'date-time-editor',
                value: '',
                error: ''
            }
        };

        this.initExtraFields(form, data.extraFields);

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

        if (this.isGta()) {
            delete form.person;
            if (!this.isAdmin() && this.isEdit) {
                delete form.tags;
            }

            if (!data.isEdit) {
                form.uploads = {
                    name: 'uploads',
                    label: i18n.gettext('File'),
                    editor: 'dropzone-editor',
                    value: '',
                    error: ''
                };
            }
        }

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
        doRequest: function (action) {
            var self = this,
                $submit = $(this.$els.submit),
                formData = this.getFormData(),
                url = API.tasks + (!!self.instance ? self.instance.id + '/edit/' : 'add/');

            $submit.toggleBtnLoading(true);

            if (!!formData.uploads) {
                var postData = new FormData();

                _.forEach(formData, function(v, k) {
                    if (v instanceof FileList) {
                        _.forEach(v, function (file) {
                            postData.append(k + '[]', file);
                        });
                    } else if (!_.isEmpty(v)) {
                        postData.append(k, v);
                    }
                });

                $.ajax({
                    url: url,
                    type: 'POST',
                    data: postData,
                    processData: false,
                    contentType: false,
                    dataType: 'json'
                }).done(function (response) {
                    $submit.toggleBtnLoading(false);
                    Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New task added'));
                    self.$dispatch('taskSaved', action, response);
                }).fail(function (response) {
                    $submit.toggleBtnLoading(false);
                    self.handleFormErrors(
                        response,
                        i18n.gettext('Could not save the task. Please try again or contact support.')
                    );
                });
            } else {
                $.ajax({
                    url: url,
                    type: 'POST',
                    data: JSON.stringify(formData),
                    contentType: 'application/json',
                    dataType: 'json'
                }).done(function (response) {
                    $submit.toggleBtnLoading(false);
                    Utils.notify(self.isEdit ? i18n.gettext('Changes saved'): i18n.gettext('New task added'));
                    self.$dispatch('taskSaved', action, response);
                }).fail(function (response) {
                    $submit.toggleBtnLoading(false);
                    self.handleFormErrors(
                        response,
                        i18n.gettext('Could not save the task. Please try again or contact support.')
                    );
                });
            }
        },
        submit: function () {
            this.doRequest();
        },
        submitAndAddMore: function () {
            this.doRequest('addMore');
        },
        submitAndGoTo: function () {
            this.doRequest('goTo');
        }
    }
});
