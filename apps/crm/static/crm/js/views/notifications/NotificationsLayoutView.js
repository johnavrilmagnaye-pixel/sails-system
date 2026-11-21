Views.notifications.NotificationsLayoutView = Vue.extend({
    template: '#notifications-layout-tmpl',

    mixins: [Mixins.CommonMixin],

    data: function () {
        return {
            notificationsApiUrl: API.notifications,
            notifications: []
        }
    },

    route: {
        data: function (transition) {
            var self = this;

            return $.when(
                $.getJSON(this.notificationsApiUrl)
            ).then(function (notificationsData) {
                self.notifications = notificationsData;
            });
        }
    },

    ready: function () {
        $(document).on('click', '.notification-item a', function (e) {
            e.preventDefault();

            var $link = $(this),
                href = $link.attr('href');

            router.go(href);
        });

        setTimeout(this.fetchNotications, 60000);
    },

    methods: {
        fetchNotications: function () {
            var self = this;

            $.getJSON(
                this.notificationsApiUrl
            ).done(function (response) {
                if (self.notifications.length !== response.length) {
                    self.notifications = response;
                }

                setTimeout(self.fetchNotications, 60000);
            });
        },
        hideNotification: function (notification) {
            var self = this;

            $.post(
                notification.hide_url
            ).done(function (data) {
                if (data['success']) {
                    self.notifications.$remove(notification);
                }
            });
        },
        hideAll: function () {
            var self = this;

            $.post(
                '/notifications/hide_all/'
            ).done(function (data) {
                if (data['success']) {
                    self.notifications = [];
                }
            });
        }
    },

    watch: {
        notifications: function () {
            var showIndicator = !!this.notifications.length;
            $('.notifications-indicator').toggleClass('hidden', !showIndicator);
        }
    }
});
