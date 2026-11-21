Views.common.CardNotesView = Vue.extend({
    template: '#card-notes-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin],

    props: ['notes', 'item', 'cardTab'],
    data: function () {
        return {
            files: [],
            maxFileSize: 20 * 1024 * 1024
        }
    },

    ready: function () {
        var self = this,
            $dropzone = $(this.$els.dropzone),
            $dropzoneInput = $(this.$els.dropzoneInput);

        $dropzoneInput.on('change', this.onInputChange);

        $dropzone.on('dragover', function(e) {
            $dropzone.toggleClass('active', true);
        }).on('dragleave drop', function(e) {
            $dropzone.toggleClass('active', false);
        }).on('drop', function(e) {
            var files = e.originalEvent.dataTransfer.files;

            // exclude not accepted and too large files
            self.files = _.filter(files, function(file) {
                return file.size <= self.maxFileSize;
            });
        });
    },

    beforeDestroy: function () {
        $(this.$els.dropzone).off();
    },

    methods: {
        addNote: function (e) {
            var self = this,
                $submit = $(this.$els.submit),
                $text = $(this.$els.text),
                postData = new FormData();

            postData.append('text', $text.val());
            if (this.files.length) {
                this.files.forEach(function (file, index) {
                    postData.append('file_' + index, file);
                });
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                url: this.$parent.itemsApiUrl + this.item.id + '/add_note/',
                type: 'POST',
                data: postData,
                processData: false,
                contentType: false
            }).done(function (response) {
                $(self.$els.dropzoneInput).val('');
                $(self.$els.text).val('');
                self.files = [];
                $submit.toggleBtnLoading(false);
                self.notes.unshift(response.note);
                Utils.notify(i18n.gettext('Note created'), 'success');
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not create the note'), 'error');
            });
        },
        deleteNote: function (note) {
            var self = this;

            $.ajax({
                url: API.notes + note.id + '/delete/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.notes.$remove(note);
                Utils.notify(i18n.gettext('Note deleted'), 'success');
            });
        },
        onInputChange: function() {
            var self = this,
                $dropzoneInput = $(this.$els.dropzoneInput),
                files = $dropzoneInput[0].files;

            // exclude too large files
            this.files = _.filter(files, function(file) {
                if (file.size > self.maxFileSize) {
                    App.notify(
                        i18n.gettext('Image ') + file.name + i18n.gettext(' is too large.\n') + self.maxFileSizeText,
                        'error'
                    );
                    return false;
                }

                return true;
            });
        }
    }
});
