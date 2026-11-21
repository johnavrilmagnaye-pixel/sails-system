var Storage = {
    accountId: null,

    configure: function (accountId) {
        this.accountId = String(accountId);
    },

    parse: function (key, defaultValue) {
        var value = localStorage.getItem(key);

        if (value === null) {
            return defaultValue;
        }

        try {
            return JSON.parse(value);
        } catch (error) {
            localStorage.removeItem(key);
            return defaultValue;
        }
    },

    commonKey: function (key) {
        return 'crm:global:' + key;
    },

    screen: function () {
        return window.location.pathname.split('/')[1] || 'shell';
    },

    accountKey: function (key) {
        if (this.accountId === null) {
            throw new Error('Storage must be configured with an account id');
        }
        return ['crm', this.accountId, this.screen(), key].join(':');
    },

    // global
    saveCommon: function (key, item) {
        localStorage.setItem(this.commonKey(key), JSON.stringify(item));
    },
    fetchCommon: function (key, defaultValue) {
        var storageKey = this.commonKey(key),
            item = this.parse(storageKey, null);

        // Preserve the only pre-stage-5 global preference and retire its old key.
        if (item === null && key === 'isSidebarCollapsed') {
            item = this.parse(key, null);
            if (item !== null) {
                this.saveCommon(key, item);
                localStorage.removeItem(key);
            }
        }

        return item !== null ? item : defaultValue;
    },

    // tenant-scoped page state
    save: function (key, item) {
        localStorage.setItem(this.accountKey(key), JSON.stringify(item));
    },
    fetch: function (key, defaultValue) {
        var item = this.parse(this.accountKey(key), null);
        return item !== null ? item : defaultValue;
    },
    fetchProperty: function (key, property, defaultValue) {
        var item = this.parse(this.accountKey(key), null);
        return item !== null && item[property] !== undefined ? item[property] : defaultValue;
    }
};
