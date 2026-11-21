Views.common.CardUploadsView = Vue.extend({
    template: '#card-uploads-tmpl',
    replace: true,

    mixins: [Mixins.CommonMixin],

    props: ['uploads', 'item', 'cardTab'],
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

        $dropzone.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
        }).on('dragover', function(e) {
            $dropzone.toggleClass('active', true);
        }).on('dragleave drop', function(e) {
            $dropzone.toggleClass('active', false);
        }).on('drop', function(e) {
            var files = e.originalEvent.dataTransfer.files;

            // exclude not accepted and too large files
            self.files = _.filter(files, function(file) {
                return file.size <= self.maxFileSize;
            });

            if (self.files.length) {
                self.handleFiles();
            }
        });
    },

    beforeDestroy: function () {
        $(this.$els.dropzone).off();
    },

    methods: {
        handleFiles: function() {
            var self = this,
                postData = new FormData();

            this.files.forEach(function (file, index) {
                postData.append('file_' + index, file);
            });

            $.ajax({
                url: this.$parent.itemsApiUrl + this.item.id + '/add_upload/',
                type: 'POST',
                data: postData,
                processData: false,
                contentType: false
            }).done(function (response) {
                $(self.$els.dropzoneInput).val('');

                response.uploads.forEach(function(upload) {
                    self.uploads.unshift(upload);
                });

                Utils.notify(response.uploads.length > 1 ? i18n.gettext('Files uploaded') : i18n.gettext('File uploaded'), 'success');
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not upload the file'), 'error');
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

            if (this.files.length) {
                this.handleFiles();
            }
        },
        deleteUpload: function (upload) {
            var self = this;

            $.ajax({
                url: API.uploads + upload.id + '/delete/',
                type: 'POST',
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                self.uploads.$remove(upload);
                Utils.notify(i18n.gettext('File deleted'), 'success');
            });
        }
    }
});
