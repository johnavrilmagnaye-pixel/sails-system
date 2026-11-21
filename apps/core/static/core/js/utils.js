var Utils = {
    removeUrlParams: function (url) {
        return url.substring(0, url.indexOf('?'));
    },

    notify: function (msg, type, timeout) {
        var $messages = $('.messages'),
            messageType = type || 'success',
            $newMsg = $('<li>').attr({
                role: messageType === 'error' ? 'alert' : 'status'
            }),
            $icon = $('<i>').addClass('fa fa-circle').attr('aria-hidden', 'true'),
            $text = $('<div>').text(msg);

        $newMsg.addClass(messageType).append($icon, $text);

        if (!timeout) {
            timeout = 5000;
        }

        $messages.prepend($newMsg);

        setTimeout(function() {
            $newMsg.remove();
        }, timeout);
    },

    pluralize: function (number, singular, plural) {
        return i18n.ngettext(singular, plural, number);
    },


    getResponseErrorMsg: function (response) {
        var msg;

        if (response.responseJSON && response.responseJSON.error) {
            msg = response.responseJSON.error;
        }

        return msg;
    }
};
