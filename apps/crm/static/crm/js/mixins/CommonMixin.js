Mixins.CommonMixin = {
    methods: {
        hasPerm: function (perm) {
            return (
                this.$root.currentUser.is_admin ||
                _.pluck(this.$root.currentUser.permissions, 'codename').indexOf(perm) > -1
            );
        },
        isCreator: function (item) {
            return this.$root.currentUser.user_id === item.user_id;
        },
        isResponsible: function (item) {
            return _.pluck(item.responsibles, 'id').indexOf(this.$root.currentUser.user_id) > -1
        },
        isAdmin: function () {
            return this.$root.currentUser.is_admin;
        },
        isOwner: function () {
            return this.$root.currentUser.is_owner;
        },
        isGta: function () {
            return this.$root.currentAccount.name === 'gta';
        },
        isEmpty: function (value) {
            return _.isEmpty(value);
        },
        canEditItem: function (contentType, item) {
            return (
                this.isAdmin() ||
                this.hasPerm('change_all_' + contentType) ||
                (this.isResponsible(item) && this.hasPerm('change_assigned_' + contentType)) ||
                (this.isCreator(item) && this.hasPerm('change_own_' + contentType))
            );
        },
        canDeleteItem: function (contentType, item) {
            return (
                this.isAdmin() ||
                (this.isCreator(item) && hasPerm('delete_own_' + contentType))
            );
        },
        canChangeDealStage: function (deal) {
            return (
                this.isAdmin() ||
                this.isCreator(deal) ||
                this.isResponsible(deal) ||
                this.hasPerm('change_all_deal')
            );
        },
        canChangeTaskState: function (task) {
            return (
                this.isAdmin() ||
                this.isCreator(task) ||
                this.isResponsible(task) ||
                this.hasPerm('change_all_task')
            );
        },

        copyText: function (e) {
            var $el = $(e.currentTarget),
                text = $el.text(),
                $copyInput = $('.copy-input');

            $copyInput.val(text.trim());
            $copyInput.select();

            document.execCommand('copy');

            Utils.notify(i18n.gettext('Copied'), 'success', 700);
        },

        generateItemName: function (item) {
            return '#' + (item.id || item.item_id) + ' ' + item.name;
        }
    },

    filters: {
        existing: function (value, item) {
            return _.filter(value, function (field) {
                return !!item.extra_fields[field.codename];
            });
        }
    }
};
