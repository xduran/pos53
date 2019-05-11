odoo.define('pos_restaurnt_ext.waiter', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    var formats = require('web.formats');
    var core = require('web.core');
    var QWeb = core.qweb;
    var Backbone = window.Backbone;
    var _t = core._t;


    models.load_models({
        model: 'pos.waiter',
        fields: ['name'],
        loaded: function(self,waiter_list){
            self.waiter_list = waiter_list;
        },
    });


    var PrintedJob = Backbone.Model.extend({
        initialize: function(attr,options){
            this.pos   = options.pos;
            this.order = options.order;
            if (options.json) {
                this.init_from_JSON(options.json);
                return;
            }
            this.time = options.time;
            this.printer   = options.printer;
             
        },
    });
    
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            _super_order.initialize.call(this,attr,options);
            if (this.pos.config.iface_waiter) {
                this.waiter = this.waiter || false;
                this.waiter_id = this.waiter_id || false;
            }
            
        },
        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.call(this);
            if (this.pos.config.iface_waiter) {
                json.waiter = this.waiter;
                json.waiter_id = this.waiter_id;
            }
            json.printed_jobs = this.printed_jobs;
            return json;
        },
        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this, arguments);
            if (this.pos.config.iface_waiter) {
                this.waiter = json.waiter;
                this.waiter_id = json.waiter_id;
            }
        },
        set_waiter: function(waiter) {
            this.waiter = waiter;
            this.waiter_id = waiter.id;
            this.trigger('change', this);
        },
        get_waiter: function() {
            return this.waiter || false;
        },
        build_line_resume: function(){
            var self = this;
            var resume = {};
            this.orderlines.each(function(line){
                if (line.mp_skip) {
                    return;
                }
                var line_hash = line.get_line_diff_hash();
                var qty  = Number(line.get_quantity());
                var note = line.get_note();
                var garnish = line.get_garnish_text();
                var product_id = line.get_product().id;

                if (line.get_product().to_garnish && line.get_product().order_separated){
                    var hashes = line.get_garnish_hashes();
                    for (var i=0; i<hashes.length; i++){
                        if(typeof resume[hashes[i][0]] === 'undefined'){
                            resume[hashes[i][0]] = { qty: qty, product_id: hashes[i][1], garnish: line.get_product().display_name, note: '' };
                        }
                        else {
                            resume[hashes[i][0]].qty += qty;
                        }
                    }
                }
                else{
                    if (typeof resume[line_hash] === 'undefined') {
                        resume[line_hash] = { qty: qty, note: note, product_id: product_id, garnish: garnish };
                    } else {
                        resume[line_hash].qty += qty;
                    }
                }

            });
            return resume;
        },
        computeChanges: function(categories){
            var current_res = this.build_line_resume();
            var old_res     = this.saved_resume || {};
            var json        = this.export_as_JSON();
            var add = [];
            var rem = [];
            var line_hash;
    
            for ( line_hash in current_res) {
                var curr = current_res[line_hash];
		if (this.pos.db.get_product_by_id(curr.product_id).pos_categ_id[1]){
                    var curr_cat = '[' + this.pos.db.get_product_by_id(curr.product_id).pos_categ_id[1].split(' / ')[1] + '] ';
                }
                else{
                    var curr_cat = '[]'
                }             
		var old  = old_res[line_hash];    
                if (typeof old === 'undefined') {
                    add.push({
                        'id':       curr.product_id,
                        'name':     curr_cat + this.pos.db.get_product_by_id(curr.product_id).display_name,
                        'note':     curr.note,
                        'garnish':  curr.garnish,
                        'qty':      curr.qty,
                    });
                } else if (old.qty < curr.qty) {
                    add.push({
                        'id':       curr.product_id,
                        'name':     curr_cat + this.pos.db.get_product_by_id(curr.product_id).display_name,
                        'note':     curr.note,
                        'garnish':  curr.garnish,
                        'qty':      curr.qty - old.qty,
                    });
                } else if (old.qty > curr.qty) {
                    rem.push({
                        'id':       curr.product_id,
                        'name':     curr_cat + this.pos.db.get_product_by_id(curr.product_id).display_name,
                        'note':     curr.note,
                        'garnish':  curr.garnish,
                        'qty':      old.qty - curr.qty,
                    });
                }
            }
    
            for (line_hash in old_res) {
                if (typeof current_res[line_hash] === 'undefined') {
                    var old = old_res[line_hash];
                    var old_cat = '[' + this.pos.db.get_product_by_id(old.product_id).pos_categ_id[1].split(' / ')[1] + '] ';
                    rem.push({
                        'id':       old.product_id,
                        'name':     old_cat + this.pos.db.get_product_by_id(old.product_id).display_name,
                        'note':     old.note,
                        'garnish':  old.garnish,
                        'qty':      old.qty, 
                    });
                }
            }
    
            if(categories && categories.length > 0){
                // filter the added and removed orders to only contains
                // products that belong to one of the categories supplied as a parameter
    
                var self = this;
    
                var _add = [];
                var _rem = [];
                
                for(var i = 0; i < add.length; i++){
                    if(self.pos.db.is_product_in_category(categories,add[i].id)){
                        _add.push(add[i]);
                    }
                }
                add = _add;
    
                for(var i = 0; i < rem.length; i++){
                    if(self.pos.db.is_product_in_category(categories,rem[i].id)){
                        _rem.push(rem[i]);
                    }
                }
                rem = _rem;
            }
    
            var d = new Date();
            var hours   = '' + d.getHours();
                hours   = hours.length < 2 ? ('0' + hours) : hours;
            var minutes = '' + d.getMinutes();
                minutes = minutes.length < 2 ? ('0' + minutes) : minutes;
    
            return {
                'new': add,
                'cancelled': rem,
                'table': json.table || false,
                'floor': json.floor || false,
                'name': json.name  || 'unknown order',
                'waiter': json.waiter.name  || false,
                'time': {
                    'hours':   hours,
                    'minutes': minutes,
                },
            };
            
        },
        get_subtotal_text: function(){
            var line = 'Subtotal';
            var subtotal = formats.format_value(this.get_subtotal(), {type: 'float', digits: [69, 2]});
            var space_fill = '.'.repeat(23 - subtotal.length - line.length)
            return line + space_fill + subtotal;
        },
        get_discount_text: function(){
            var line = 'Descuento(' + formats.format_value(this.get_discount_pc(), {type: 'float', digits: [69, 0]}) + '%)';
            var discount = '-' + formats.format_value(this.get_discount_amount(), {type: 'float', digits: [69, 2]});
            var space_fill = '.'.repeat(23 - discount.length - line.length)
            return line + space_fill + discount;
        },
        get_service_text: function(){
            if(this.get_service_amount()){
                var line = 'Servicio(' + formats.format_value(this.get_service_pc(), {type: 'float', digits: [69, 0]}) + '%)';
                var service = '+' + formats.format_value(this.get_service_amount(), {type: 'float', digits: [69, 2]});
                var space_fill = '.'.repeat(23 - service.length - line.length)
                return line + space_fill + service;
            }
            return '';
        },
        get_total_text: function(){
            var line = 'TOTAL';
            var total = formats.format_value(this.get_total_with_tax() - this.get_tip(), {type: 'float', digits: [69, 2]});
            var space_fill = '.'.repeat(23 - total.length - line.length)
            return line + space_fill + total;
        },
        get_change_text: function(){
            var line = 'Cambio';
            var change = formats.format_value(this.get_change(), {type: 'float', digits: [69, 2]});
            var space_fill = '.'.repeat(23 - change.length - line.length)
            return line + space_fill + change;
        },
        get_tip_text: function(){
            var line = 'Propina';
            var tip = formats.format_value(this.get_tip(), {type: 'float', digits: [69, 2]});
            var space_fill = '.'.repeat(23 - tip.length - line.length)
            return line + space_fill + tip;
        },
        export_for_printing: function(){
            var result = _super_order.export_for_printing.call(this);
            result.waiter = this.waiter.name;
            result.subtotal_text = this.get_subtotal_text();
            result.discount_text = this.get_discount_text();
            result.service_text = this.get_service_text();
            result.total_text = this.get_total_text();
            result.change_text = this.get_change_text();
            result.tip_text = this.get_tip_text();
            return result;
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        get_string_to_print: function() {
            var amount = formats.format_value(this.get_display_price(), {type: 'float', digits: [69, 2]});
            var product = this.get_quantity_str()  + '. ' + this.get_product().display_name;
            product = product.slice(0, 30 - amount.length)
            var space_fill = '.'.repeat(32 - product.length - amount.length)
            return product + space_fill + amount;
        },
        export_for_printing: function() {
            var result = _super_orderline.export_for_printing.call(this);
            result.string_to_print = this.get_string_to_print();
            result.garnish = this.get_garnish_text();
            return result;
        },
        get_line_diff_hash: function(){
            var diff_hash = _super_orderline.get_line_diff_hash.call(this);
            if (this.get_garnish()) {
               diff_hash = diff_hash + '|' + this.get_garnish_text();
            }
            return diff_hash;
        },
    });

    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        get_string_to_print: function() {
            var amount = formats.format_value(this.get_amount(), {type: 'float', digits: [69, 2]});
            var payment = this.name;
            payment = payment.slice(0, 23 - amount.length)
            var space_fill = '.'.repeat(23 - payment.length - amount.length)
            return payment + space_fill + amount;
        },
        export_for_printing: function() {
            var result = _super_paymentline.export_for_printing.call(this);
            result.string_to_print = this.get_string_to_print();
            return result;
        },
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_waiter: function() {
            var order = this.get_order();
            if (order) {
                return order.get_waiter();
            }
            return null;
        },
    });

    var WaiterButton = screens.ActionButtonWidget.extend({
        template: 'WaiterButton',

        button_click: function() {
            //this.altlight(this.pos.get_order().toggle_service());
            var self = this;
            var list = [];
            for (var i = 0; i < this.pos.waiter_list.length; i++) {
                var waiter = this.pos.waiter_list[i];
                list.push({
                    'label': waiter.name,
                    'item':  waiter,
                });
            }

            this.gui.show_popup('selection',{
                'title': _t('Select Waiter'),
                list: list,
                confirm: function(waiter){
                    self.pos.get_order().set_waiter(waiter);
                    self.renderElement();
                },
            });
        },
    });

    screens.define_action_button({
            'name': 'waiter',
            'widget': WaiterButton,
            'condition': function(){
                return this.pos.config.iface_waiter;
            },
        }
    );

    screens.ProductScreenWidget.include({

        show: function(){
            this._super();
            if (this.pos.config.iface_waiter){
                this.action_buttons['waiter'].renderElement();
            }
        }
    });

    screens.ProductScreenWidget.include({
        show: function(){
            this._super();
            //Fixme: this isn't working properly
            if (!this.pos.config.iface_guest_count){
                this.action_buttons['guests'].hide();
            }
        }
    });

    return {
        WaiterButton: WaiterButton
    }
});
