(function($) {

    /***
     *
     * @param state: true - toggle disable state off, false - toggle disable state on
     */
    $.fn.toggleBtnState = function (state) {
        this.prop('disabled', !state);
        this.toggleClass('disabled', !state);
    };

    /***
     *
     * @param state: true - toggle loading on, false - toggle loading off
     */
    $.fn.toggleBtnLoading = function (state) {
        this.toggleBtnState(!state);

        if (!this.find('.spinner-w').length) {
            this.append('<span class="spinner-w"><i class="fa fa-spinner fa-spin"></i></span>');
        }

        this.toggleClass('btn-loading', state);
    };

})($);
