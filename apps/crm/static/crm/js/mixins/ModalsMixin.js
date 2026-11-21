Mixins.ModalsMixin = {
    methods: {
        initModals: function() {
            return {

            }
        }
    },

    events: {
        modalCanceled: function (modalName) {
            if (!this.modals) {
                return;
            }

            this.modals[modalName].show = false;
        }
    }
};
