odoo.define('pos_restaurant_changes_control.delete_control', function (require) {
"use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.printed_quantity = this.printed_quantity || false;
            this.printed_price_unit = this.printed_price_unit || false;
            this.printed_discount = this.printed_discount || false;
            this.printed = this.printed || false;
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.call(this);
            json.printed_quantity = this.printed_quantity;
            json.printed_price_unit = this.printed_price_unit;
            json.printed_discount = this.printed_discount;
            json.printed = this.printed;
            return json;
        },
        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.printed_quantity = json.printed_quantity;
            this.printed_price_unit = json.printed_price_unit;
            this.printed_discount = json.printed_discount;
            this.printed = json.printed;
        },
        has_printed_differences: function(){
            if (this.printed){
                if(this.printed_quantity != this.quantity){
                    return true
                }
                if(this.printed_price_unit != this.price){
                    return true
                }
                if(this.printed_discount != this.discount){
                    return true
                }
            }
            return false
        },
        mark_as_printed: function(){
            this.printed_quantity = this.quantity;
            this.printed_price_unit = this.price;
            this.printed_discount = this.discount;
            this.printed = true;
            this.trigger('change', this);
        },
        get_difference_data: function(){
            var line = {};
            line.product_id = this.product.id;
            line.printed_quantity = this.printed_quantity;
            line.final_quantity = this.quantity;
            line.printed_price_unit = this.printed_price_unit;
            line.final_price_unit = this.price;
            line.printed_discount = this.printed_discount;
            line.final_discount = this.discount;
            return line;
        },
    });


    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            _super_order.initialize.call(this,attributes,options);
            this.printed = this.printed || false;
            this.printed_times = this.printed_times || 0;
            this.changed_lines = [];
        },
        mark_as_printed: function(){
            this.printed = true;
            var order_lines = this.get_orderlines();
            for(var i=0; i<order_lines.length; i++){
                order_lines[i].mark_as_printed();
            }
            this.printed_times++;
        },
        add_deleted_line: function(line){
            this.changed_lines.push(line);
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            this.changed_lines = json.changed_lines;
            this.printed = json.printed;
            this.printed_times = json.printed_times;

        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.call(this);
            json.changed_lines = this.changed_lines;
            json.printed = this.printed;
            json.printed_times = this.printed_times;
            return json;
        },
        destroy: function(){
            if(this.printed){
                var  lines = this.changed_lines;
                var self = this;
                var order_lines = this.get_orderlines();
                if(!this.is_paid()){
                //    for(var i=0; i<order_lines.length; i++){
                //        if (order_lines[i].has_printed_differences() || !order_lines[i].printed){
                //            var item = order_lines[i].get_difference_data();
                //            item.session_id = order_lines[i].pos.pos_session.id;
                //            item.table_id = order_lines[i].pos.get_order().table.id;
                //            self.add_deleted_line(item);
                //        }
                //    }
                //}
                //else{
                    for(var i=0; i<order_lines.length; i++){
                        if (order_lines[i].printed){
                            var item = order_lines[i].get_difference_data();
                            item.session_id = order_lines[i].pos.pos_session.id;
                            item.table_id = order_lines[i].pos.get_order().table.id;
                            item.final_quantity = 0;
                            lines.push(item);
                        }
                    }
                    if(lines.length){
                        var model = new Model('pos.changed.line');
                        model.call('create_from_ui',[lines]);
                    }
                }

            }
            _super_order.destroy.call(this);
        },
    });

    screens.PaymentScreenWidget.include({
        validate_order: function(force_validation){
            var order = this.pos.get_order();
            if (order.printed){
                var order_lines = order.get_orderlines();
                for(var i=0; i<order_lines.length; i++){
                    if (order_lines[i].has_printed_differences() || !order_lines[i].printed){
                        var item = order_lines[i].get_difference_data();
                        item.session_id = order_lines[i].pos.pos_session.id;
                        item.table_id = order.table.id;
                        order.add_deleted_line(item);
                    }
                }
            }
            this._super(force_validation);
        },

    });

    screens.OrderWidget.include({
        remove_orderline: function(order_line){
            this._super(order_line);
            var order = this.pos.get_order();
            if(order_line.printed){
                var item = order_line.get_difference_data();
                item.session_id = order_line.pos.pos_session.id;
                item.table_id = order_line.pos.get_order().table.id;
                order.add_deleted_line(item);
            }
        },
    });

    screens.ProductScreenWidget.include({
        start: function(){
            this._super();
            var self = this;

            // maybe this isn't the best way to get in,
            //  but its the only one I found
            if (this.pos.config.iface_changes_control ){
                var PrintBillButton = $('.order-printbill');
                PrintBillButton.bind('click', function(){
                    self.pos.get_order().mark_as_printed();
                });
            }
        },
    });


});
