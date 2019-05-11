odoo.define('pos_ext.pos_ext', function (require) {
"use strict";


    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var Model = require('web.DataModel');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var _ = require('_');

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            _super_order.initialize.call(this,attr,options);
            this.note = this.note || '';
        },
        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.call(this);
            json.note = this.note;
            return json;
        },
        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this, arguments);
            this.note = json.note;
        },
        get_note: function(){
			return this.note;
		},
		set_note: function(note){
			this.note = note;
		},  
    });

    screens.PaymentScreenWidget.include({
        show: function(){
            this._super();
            this.update_input();
        },
        update_input: function(){
            var self = this;
            var contents = this.$('.pos-order-note-div');
            contents.find('.pos-order-note').on('keyup',function(event){
					self.pos.get('selectedOrder').set_note(this.value);
                });
        },
    })


    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        strip_quantity_str: function(qty_str){
            return _.str.strip(_.str.strip(qty_str, '0'),'.');
        },
        get_quantity_str: function() {
            var result = _super_orderline.get_quantity_str.call(this);
            return this.strip_quantity_str(result);
        },
        get_quantity_str_with_unit: function(){
            var result = _super_orderline.get_quantity_str_with_unit.call(this);
            return this.strip_quantity_str(result);
        },

    });
    chrome.Chrome.include({
        build_widgets: function() {
            this._super();
            if(!this.pos.config.iface_change_cashier){
                this.$('.username').addClass('hidden');
            }
        },
    });


});
