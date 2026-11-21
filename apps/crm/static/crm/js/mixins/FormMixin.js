Mixins.FormMixin = {
    methods: {
        initExtraFields: function (form, extraFields) {
            _.each(extraFields, function(extraField) {
                var fieldData = {
                    name: extraField.codename,
                    label: extraField.name,
                    value: '',
                    error: ''
                };

                switch (extraField.type) {
                    case Const.EXTRA_FIELD_TYPES.STRING:
                        fieldData.editor = 'text-editor';
                        break;
                    case Const.EXTRA_FIELD_TYPES.TEXT:
                        fieldData.editor = 'text-area-editor';
                        fieldData.cols = 40;
                        fieldData.rows = 10;
                        break;
                    case Const.EXTRA_FIELD_TYPES.SELECT:
                        fieldData.editor = 'select-editor';
                        fieldData.options = extraField.options;
                        break;
                    case Const.EXTRA_FIELD_TYPES.DATE:
                        fieldData.editor = 'date-editor';
                        break;
                    case Const.EXTRA_FIELD_TYPES.DATETIME:
                        fieldData.editor = 'date-time-editor';
                        break;
                    case Const.EXTRA_FIELD_TYPES.NUMBER:
                        fieldData.editor = 'text-editor';
                        fieldData.inputType = 'number';
                        break;
                    case Const.EXTRA_FIELD_TYPES.PHONES:
                        fieldData.editor = 'phone-list-editor';
                        fieldData.inputClass = 'phone-input';
                        fieldData.defaultValue = [''];
                        fieldData.value = [''];
                        fieldData.items = [{id: 0, value: ''}];
                        break;
                    case Const.EXTRA_FIELD_TYPES.EMAILS:
                        fieldData.editor = 'list-editor';
                        fieldData.inputType = 'email';
                        fieldData.defaultValue = [''];
                        fieldData.value = [''];
                        fieldData.items = [{id: 0, value: ''}];
                        break;
                }

                form[extraField.codename] = fieldData;
            });
        },

        setInstanceValues: function (form, instance) {
            var self = this;

            _.forOwn(form, function (field, fieldName) {
                var instanceValue;

                if (fieldName.indexOf('extra_field') > -1) {
                    instanceValue = instance.extra_fields[fieldName];
                } else {
                    instanceValue = instance[fieldName]
                }

                if (!instanceValue) {
                    return;
                }

                switch (field.editor) {
                    case 'select-editor':
                        if (_.isArray(instanceValue)) {
                            if (!!self.modalData && self.modalData.modalName === 'periodicTaskForm') {
                                if (
                                    (fieldName === 'weekdays' && instanceValue.length === 7) ||
                                    (fieldName === 'months' && instanceValue.length === 12)
                                ) {
                                    field.value = [0]
                                } else {
                                    field.value = instanceValue;
                                }
                            } else {
                                field.options = _.map(instanceValue, function (val) {
                                    return {id: val.id, text: val.name};
                                });
                                field.value = _.map(instanceValue, function (val) {
                                    return val.id;
                                });
                            }
                        } else {
                            if (_.isEmpty(field.options)) {
                                field.options = [{id: instanceValue.id, text: instanceValue.name}];
                                field.value = instanceValue.id;
                            } else {
                                field.value = instanceValue;
                            }
                        }
                        break;
                    case 'date-editor':
                        field.value = moment(instanceValue).format('DD.MM.YYYY');
                        break;
                    case 'date-time-editor':
                        field.value = moment(instanceValue).format('DD.MM.YYYY HH:mm');
                        break;
                    case 'time-editor':
                        field.value = moment(instanceValue, 'HH:mm').format('HH:mm');
                        break;
                    case 'list-editor':
                    case 'phone-list-editor':
                        field.value = instanceValue;

                        if (!!field.value.length) {
                            field.items = _.map(instanceValue, function (option, index) {
                                return {
                                    id: index,
                                    value: option
                                }
                            });
                        } else {
                            field.items = [{id: 0, value: ''}]
                        }

                        break;
                    default:
                        field.value = instanceValue;
                }
            });
        },

        getFormData: function () {
            var formData = {};

            _.forEach(this.form, function(field) {
                if (field.name === 'responsibles' && !!field.value && !_.isArray(field.value)) {
                    field.value = [field.value];
                }
                //if (field.editor === 'date-time-editor') {
                  //  field.value = moment(field.value).utc().format();
                //}

                formData[field.name] = field.value;
            });

            return formData;
        },

        getResponseFormErrors: function (response) {
            var errors;

            if (response.responseJSON && response.responseJSON.errors) {
                errors = response.responseJSON.errors;
            }

            return errors;
        },

        handleFormErrors: function (response, defaultErrorMsg) {
            var msg = Utils.getResponseErrorMsg(response);

            if (msg) {
                Utils.notify(msg, 'error');
                return;
            }

            var self = this,
                errors = this.getResponseFormErrors(response);

            if (errors) {
                _.forOwn(errors, function (value, key) {
                    self.form[key].error = _.isArray(value) ? value[0] : value;
                });
                return;
            }

            Utils.notify(defaultErrorMsg, 'error');
        }

    }
};
