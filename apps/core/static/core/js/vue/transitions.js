Vue.transition('hide', {
    enter: function (el, done) {
        $(el).removeClass('hidden');
    },
    leave: function (el, done) {
        $(el).addClass('hidden');
    }
});

Vue.transition('fade', {
    enter: function (el, done) {
        $(el).css('opacity', 0).animate({opacity: 1}, 400, done)
    },
    leave: function (el, done) {
        $(el).animate({opacity: 0}, 400, done)
    }
});
