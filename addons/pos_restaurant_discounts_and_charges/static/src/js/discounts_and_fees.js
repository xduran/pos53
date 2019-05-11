odoo.define('pos_restaurant_discounts_and_charges.discounts_and_fees', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var core = require('web.core');
    var utils = require('web.utils');

    var _t = core._t;
    var round_pr = utils.round_precision;

    var formats = require('web.formats');


    models.load_fields("res.partner", ['pos_discount']);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            _super_order.initialize.call(this,attr,options);
            if (this.pos.config.iface_allow_tip) {
                this.tip = this.tip || 0;
            }
            if (this.pos.config.iface_global_discount) {
                this.discount_pc = this.discount_pc || 0;
                this.discount_amount = this.discount_amount || 0;
            }
            if (this.pos.config.iface_service_fee){
                this.service_pc = this.service_pc || 0;
                this.service_amount = this.service_amount || 0;
            }
        },
        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.call(this);
            if (this.pos.config.iface_allow_tip) {
                json.tip = this.tip;
            }
            if (this.pos.config.iface_global_discount) {
                json.discount_pc = this.discount_pc;
                json.discount_amount = this.discount_amount;
            }
            if (this.pos.config.iface_service_fee) {
                json.service_pc = this.service_pc;
                json.service_amount = this.service_amount;
            }
            return json;
        },
        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this, arguments);
            if (this.pos.config.iface_allow_tip) {
                this.tip = json.tip;
            }
            if (this.pos.config.iface_global_discount) {
                this.discount_pc = json.discount_pc;
                this.discount_amount = json.discount_amount;
            }
            if (this.pos.config.iface_service_fee) {
                this.service_pc = json.service_pc;
                this.service_amount = json.service_amount;
            }
        },
        set_tip: function(tip) {
            this.tip = tip;
            this.trigger('change', this);
        },
        get_tip: function() {
            return this.tip || 0;
        },
        is_tip_set: function() {
            if (this.tip > 0){
                return true;
            }
            return false;
        },
        set_client: function(client){
            _super_order.set_client.apply(this, arguments);
            if(client){
                this.set_discount_pc(client.pos_discount);
                if(client.pos_discount >= 100){
                    this.set_service_pc(0);
                }
            }
            else{
                this.set_discount_pc(0);
            }
        },
        set_discount_pc: function(discount_pc){
            this.discount_pc = parseInt(discount_pc * 100) / 100;
            //this.discount_pc = round_pr(discount_pc, 0.01);
            this.trigger('change', this);
        },
        get_discount_pc: function(){
            return this.discount_pc;
        },
        get_discount_amount: function(){
            var amount = parseInt(this.get_subtotal() * this.discount_pc);
            if (amount%5){
                amount = amount + 5 - amount % 5;
            }
            this.discount_amount = amount / 100;
            return this.discount_amount;
        },
        set_service_pc: function(service_pc){
            this.service_pc = service_pc;
            this.trigger('change', this);
        },
        get_service_pc: function(){
            return this.service_pc;
        },
        get_service_amount: function(){
            var amount = parseInt(this.get_subtotal() * this.service_pc);
            if (amount%5){
                amount = amount + 5 - amount % 5;
            }
            this.service_amount = amount / 100;
            return this.service_amount;
        },
        toggle_service: function(){
            if(this.service_pc){
                this.set_service_pc(0);
                return false;
            }
            else{
                this.set_service_pc(this.pos.config.service_pc);
                return true;
            }
        },
        get_total_without_tax: function(){
            var value = _super_order.get_total_without_tax.call(this);
            if (this.pos.config.iface_global_discount) {
                value -= this.get_discount_amount();
            }
            if (this.pos.config.iface_service_fee) {
                value += this.get_service_amount();
            }
            if (this.pos.config.iface_allow_tip) {
                value += this.get_tip();
            }
            return round_pr(value, this.pos.currency.rounding);
        }

    });

    screens.PaymentScreenWidget.include({
        click_tip: function(){
            var self   = this;
            var order  = this.pos.get_order();
            var tip    = order.get_tip();
            var change = order.get_change();
            var value  = tip;

            if (tip === 0 && change > 0  ) {
                value = change;
            }

            this.gui.show_popup('number',{
                'title': tip ? _t('Change Tip') : _t('Add Tip'),
                'value': self.format_currency_no_symbol(value),
                'confirm': function(value) {

                    order.set_tip(formats.parse_value(value, {type: "float"}, 0));
                    self.order_changes();
                    self.render_paymentlines();
                    if (value > 0) {
                        self.$('.js_tip').addClass('highlight');
                    } else {
                        self.$('.js_tip').removeClass('highlight');
                    }
                }
            });

        },
    });

    screens.OrderWidget.include({
        update_summary: function(){
            this._super();
            var order = this.pos.get_order();
            if (!order.get_orderlines().length) {
                return;
            }

            var total     = order ? order.get_total_with_tax() : 0;
            var taxes     = order ? total - order.get_total_without_tax() : 0;
            var subtotal = order ? order.get_subtotal() : 0;
            var discount_pc = order ? order.get_discount_pc() : 0;
            var discount_amount = order ? order.get_discount_amount() : 0;
            var service_pc = order ? order.get_service_pc() : 0;
            var service_amount = order ? order.get_service_amount() : 0;

            var update_discount = this.pos.config.iface_global_discount;
            var update_service = this.pos.config.iface_service_fee;
            var update_taxes = this.pos.config.iface_display_taxes;

            if (update_taxes || update_service || update_discount) {
                this.el.querySelector('.summary .subtotal .value').textContent = this.format_currency(subtotal);
            }
            if (update_discount) {
                this.el.querySelector('.summary .discount .percent').textContent = '' + discount_pc;
                this.el.querySelector('.summary .discount .value').textContent = this.format_currency(discount_amount);
            }
            if (update_service){
                this.el.querySelector('.summary .service .percent').textContent = '' + service_pc;
                this.el.querySelector('.summary .service .value').textContent = this.format_currency(service_amount);
                var buttons = this.getParent().action_buttons;
                if (buttons && buttons.service) {
                    buttons.service.altlight(service_pc);
                }
            }
            if (update_taxes) {
                this.el.querySelector('.summary .taxes .value').textContent = this.format_currency(taxes);
            }
            this.el.querySelector('.summary .total1 .value').textContent = this.format_currency(total);

        },
    });

    screens.NumpadWidget.include({
        clickDiscount: function(){
            var self = this;
            this.gui.show_popup('number', {
                'title': _t('Discount(%)'),
                'cheap': false,
                'value':   this.pos.get_order().get_discount_pc(),
                'confirm': function(value) {
                    value = Math.max(0,Number(value));
                    value = Math.min(100,Number(value));
                    self.pos.get_order().set_discount_pc(value);
                },
            });
        },
        start: function() {
            this._super();
            if(this.pos.config.iface_global_discount){
                this.$el.find('.numpad-disc').click(_.bind(this.clickDiscount, this));
            }
        }
    });

    var ServiceButton = screens.ActionButtonWidget.extend({
        template: 'ServiceButton',

        button_click: function() {
            this.altlight(this.pos.get_order().toggle_service());
        },
    });

    screens.define_action_button({
            'name': 'service',
            'widget': ServiceButton,
            'condition': function(){
                return this.pos.config.iface_service_fee;
            },
        }
    );

    screens.ProductScreenWidget.include({

        show: function(){
            this._super();
            if (this.pos.config.iface_service_fee){
                this.action_buttons['service'].altlight(this.pos.get_order().get_service_pc());
            }
        }
    });

    return {
        ServiceButton: ServiceButton
    }

});
