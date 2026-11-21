function init_modal_form ($modal) {
    if ($modal.hasClass('export-modal')) {
        var $radio = $modal.find('.radio');

        $radio.each(function (index) {
            $(this).prepend($(this).find('input'));

            $(this).find('input').prop('id', 'radio' + index);
            $(this).find('label').prop('for', 'radio' + index);
        });
    }
}

function make_modal_accessible ($modal, trigger) {
    var $title = $modal.find('.modal-title, .modal-header h4, .modal-header h3').first(),
        titleId = 'loaded-modal-title-' + new Date().getTime();

    if ($title.length) {
        $title.attr('id', titleId);
        $modal.attr('aria-labelledby', titleId);
    }
    $modal.attr({
        role: 'dialog',
        'aria-modal': 'true'
    });
    $modal.one('shown.bs.modal', function () {
        var $firstControl = $modal.find(
            'input:not([disabled]):not([type="hidden"]), select:not([disabled]), ' +
            'textarea:not([disabled]), button:not([disabled]), a[href]'
        ).filter(':visible').first();

        if ($firstControl.length) {
            $firstControl.focus();
        } else {
            $modal.attr('tabindex', '-1').focus();
        }
    });
    $modal.one('hidden.bs.modal', function () {
        if (trigger && document.contains(trigger)) {
            trigger.focus();
        }
    });
}


$(document).ready(function() {
    $(document).on('click', '.show-modal-form', function (e) {
        e.stopPropagation();
        e.preventDefault();

        $('.modal:visible').modal('hide');

        var $btn = $(this),
            trigger = this,
            form_name = $btn.data('form') + '-modal',
            form_class = '.' + form_name;

        $btn.blur();

        if (!$(form_class).length) {
            $('body').append(
                $('<div>').addClass('modal ' + form_name).append(
                    $('<div>').addClass('modal-dialog').append(
                        $('<div>').addClass('modal-content')
                    )
                )
            );
        }

        var $modal = $(form_class);

        $modal.find('.modal-content').load(
            $btn.attr('href'),
            function () {
                init_modal_form($modal);
                make_modal_accessible($modal, trigger);

                $modal.modal({
                    backdrop: 'static',
                    keyboard: true
                }).modal('show');
            }
        );

        return false;
    });

    $(document).on('submit', '.modal form', function () {
        var $form = $(this);
        $form.find('.modal-footer [type=submit]').prop('disabled', true);
    });

    $(document).on('click', '.modal-form-submit-options a', function (e) {
        e.preventDefault();
        var $link = $(this);
        $link.closest('form').attr('action', $link.attr('href')).submit();
    });
});


bootbox.addLocale('gettext', {
  OK: i18n.gettext('OK'),
  CANCEL: i18n.gettext('Cancel'),
  CONFIRM: i18n.gettext('Confirm')
});

bootbox.setDefaults({
  locale: 'gettext',
  show: true,
  backdrop: true,
  closeButton: false,
  animate: false
});


$.fn.editableform.buttons = '<button type="submit" class="btn btn-success editable-submit icon-btn"><i class="fa fa-check"></i></button>'
        + '<button type="button" class="btn btn-default editable-cancel icon-btn"><i class="fa fa-times"></i></button>';

$.fn.modal.Constructor.prototype.enforceFocus = function() {};
