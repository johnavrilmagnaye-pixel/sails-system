Views.settings.SettingsTagsLayoutView = Vue.extend({
    template: '#settings-tags-layout-tmpl',

    mixins: [Mixins.CommonMixin, Mixins.FetchDataMixin, Mixins.BaseGridMixin],
    components: {
        gridPagination: Views.base.GridPaginationView
    },

    data: function () {
        return {
            itemsApiUrl: API.tags,
            items: [],
            paginationData: {
                page: 1,
                pageSize: 25,
                count: null,
                previous: null,
                next: null
            },
        }
    },

    route: {
        data: function (transition) {
            var self = this,
                queryParams = this.getFetchDataParams();

            queryParams.is_settings = true;

            return $.getJSON(this.itemsApiUrl, queryParams).done(function (tagsData) {
                self.setFetchDataResponse(tagsData);
            });
        }
    },

    methods: {
        getFetchDataParams: function () {
            return {
                page: this.paginationData.page,
                page_size: this.paginationData.pageSize,
                is_settings: true
            };
        },
        addTag: function (e) {
            var self = this,
                $form = $(e.currentTarget),
                $submit = $form.find('.btn'),
                postData = {
                    name: $form.find('input[name=name]').val()
                };

            if (!postData.name) {
                Utils.notify(i18n.gettext('Enter a tag name'), 'error');
                return;
            }

            $submit.toggleBtnLoading(true);

            $.ajax({
                type: 'POST',
                url: API.tags,
                data: JSON.stringify(postData),
                contentType: 'application/json',
                dataType: 'json'
            }).done(function (response) {
                $submit.toggleBtnLoading(false);

                self.items.unshift(response.tag);
                self.count++;
                $form.trigger('reset');

                Utils.notify(i18n.gettext('Tag created'), 'success');
            }).fail(function (response) {
                $submit.toggleBtnLoading(false);

                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not create the tag'), 'error');
            });
        },
        deleteTag: function (tag) {
            var self = this;

            $.post(
                API.tags + tag.id + '/delete/'
            ).done(function (response) {
                self.items.$remove(tag);
                self.count--;

                Utils.notify(i18n.gettext('Tag deleted'));
            }).fail(function (response) {
                var msg = Utils.getResponseErrorMsg(response);
                Utils.notify(msg || i18n.gettext('Could not delete the tag'), 'error');
            });
        }
    }
});
