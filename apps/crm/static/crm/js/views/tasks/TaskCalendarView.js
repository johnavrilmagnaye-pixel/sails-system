Views.tasks.TaskCalendarView = Vue.extend({
    template: '#task-calendar-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin, Mixins.ModalsMixin, Mixins.FetchDataMixin],
    components: {
        taskFormModal: Views.modals.TaskFormModalView
    },

    props: ['filters', 'extraFields'],
    data: function () {
        return {
            modelName: 'task',
            items: [],
            currentDate: '',
            calendarView: Storage.fetch('calendarView', 'month'), // month, week, day,
            modals: {
                taskForm: {
                    show: false,
                    data: {
                        instance: null,
                        extraFields: this.extraFields
                    }
                }
            }
        };
    },

    ready: function () {
        var self = this,
            $calendar = $(this.$els.calendar),
            $btnGroup;

        $calendar.fullCalendar({
            lang: CRMWidgetI18n.localeKey,
            header: false,
            defaultView: this.calendarView,
            timezone: 'local',
            eventLimit: true,
            allDaySlot: false,
            timeFormat: 'H:mm',
            defaultTimedEventDuration: '01:00:00',
            editable: true,
            events: {
                url: API.tasksCalendar,
                data: function() {
                    return _.pick(self.filters, _.identity);
                }
            },
            eventClick: function(calEvent, jsEvent, view) {
                router.go(calEvent.url);
                return false;
            },
            viewRender: function (view, element) {
                self.currentDate = view.title;
                self.calendarView = view.name;
                Storage.save('calendarView', view.name);
            },
            eventDrop: function(event) {
              $.ajax({
                url: API.tasks + event.task_id + '/change_date/',
                type: 'POST',
                data: JSON.stringify({
                  expire_date: event.start.format('DD.MM.YYYY HH:mm'),
                }),
                contentType: 'application/json',
                dataType: 'json'
                }).done(function (response) {
                    event.color = response.state === 3 ? '#d9534f' : '#428bca';
                    $calendar.fullCalendar('renderEvent', event);
                    Utils.notify(i18n.gettext('Task rescheduled'));
                }).fail(function (response) {
                  var msg = Utils.getResponseErrorMsg(response);
                  Utils.notify(
                    msg || i18n.gettext('Could not reschedule the task. Please try again or contact support.'),
                    'error'
                  );
                });
            },
        });

        $btnGroup = $calendar.find('.fc-button-group');
        $btnGroup.addClass('btn-group');
        $btnGroup.find('.fc-button').addClass('btn btn-default');
    },

    beforeDestroy: function () {
        $(this.$els.calendar).fullCalendar('destroy');
    },

    methods: {
        fetchData: function () {
            $(this.$els.calendar).fullCalendar('refetchEvents');
        },
        changeCalendarView: function (viewName) {
            $(this.$els.calendar).fullCalendar('changeView', viewName);
        },
        changeCalendarPage: function (direction) {
            $(this.$els.calendar).fullCalendar(direction);
        },
        toggleTaskFormModal: function (showModal, instance) {
            this.modals.taskForm.show = showModal;
            this.modals.taskForm.data.instance = instance || null;
        }
    },

    events: {
        taskSaved: function (action, data) {
            var self = this,
                $calendar = $(self.$els.calendar);

            this.toggleTaskFormModal(false);

            switch (action) {
                case 'addMore':
                    $calendar.fullCalendar('renderEvent', data.calendar_task, true);
                    setTimeout(function () {
                        self.toggleTaskFormModal(true);
                    }, 300);
                    break;
                case 'goTo':
                    this.$router.go(data.task.url);
                    break;
                default:
                    $calendar.fullCalendar('renderEvent', data.calendar_task, true);
            }
        }
    }
});
