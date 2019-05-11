odoo.define('pos_restaurant_work_order.work_order', function (require) {
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

    models.load_models({
        model: 'pos.work.order.stage',
        fields: ['name'],
        loaded: function(self,stage_list){
            self.stage_list = stage_list;
            self.stage_by_id = {};
            for (var i = 0; i < stage_list.length; i++) {
                self.stage_by_id[stage_list[i].id] = stage_list[i];
            }
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.work_order_stage = this.work_order_stage || false;
            this.work_order_id = this.work_order_id || false;
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.call(this);
            json.work_order_stage = this.work_order_stage;
            json.work_order_id = this.work_order_id;
            return json;
        },
        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.work_order_stage = json.work_order_stage;
            this.work_order_id = json.work_order_id;
        },
        clone: function(){
            var orderline = _super_orderline.clone.call(this);
            orderline.work_order_stage = this.work_order_stage;
            return orderline;
        },
        set_work_order_id: function(work_order_id){
            this.work_order_id= work_order_id;
        },
        get_work_order_id: function(){
            return this.work_order_id;
        },
        set_work_order_stage: function(stage_id){
            if (this.work_order_stage != stage_id){
                this.work_order_stage = stage_id;
                this.trigger('change', this);
            }
        },
        get_work_order_stage_name:function(){
            return this.pos.stage_by_id[this.work_order_stage].name;
        },
        get_hash_str: function(){
            var result = this.id + '-' + this.pos.get_order().table.id + '-';
            result += this.get_line_diff_hash();
            return result;
        },
        get_fields_values: function(){
            var fields = {};
            fields.id = this.get_work_order_id();
            fields.quantity = this.get_quantity();
            fields.product_id = this.get_product().id;
            fields.note = this.get_note();
            fields.table_id = this.pos.get_order().table.id;
            fields.session_id = this.pos.pos_session.id;
            fields.hash_str = this.get_hash_str();
            fields.waiter_id = this.pos.get_order().waiter.id;
            fields.garnish_ids = this.get_garnish();
            return fields;
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        destroy: function(){
            var orderlines = this.get_orderlines();
            var model = new Model('pos.work.order');
            var field_list = [];
            for(var i=0; i<orderlines.length; i++){
                var work_order_id = orderlines[i].get_work_order_id();
                var work_order_stage = orderlines[i].work_order_stage;
                //FIXME: Don't use fixed ids to map stages
                if(work_order_id && work_order_stage < 4){
                    var fields = {};

                    fields.id = work_order_id;
                    fields.hash_str = orderlines[i].get_hash_str();
                    if(this.is_paid()){
                        fields.stage_id = 4;
                    }
                    else{
                        fields.stage_id = 5;
                    }
                    field_list.push(fields);

                }
            }
            if(field_list.length){
                model.call('create_from_ui',[field_list]);
            }
            _super_order.destroy.call(this);
        },

    });

    screens.OrderWidget.include({
        init: function(parent, options) {
            this._super(parent, options);
            this.deleted_work_orders = [];
            //setTimeout(this.update_orderlines_stages(), 10000);
        },
        click_line: function(line, event) {
            if (this.mp_dbclk_time + 500 > (new Date()).getTime()) {
                if(line.work_order_stage === 3){
                    var model = new Model('pos.work.order');
                    var hash_str = line.get_hash_str();
                    var self = this;
                    var fields =[{
                        'id':line.get_work_order_id(),
                        'hash_str':hash_str,
                        'stage_id':4
                    }];
                    model.call('create_from_ui',[fields]).then(function(orders_stage){
                        if(orders_stage[hash_str]){
                            line.set_work_order_stage(orders_stage[hash_str][1]);
                        }
                    },function(err,event){
                        event.preventDefault();
                        self.pos.gui.show_popup('error',{
                            'titexport_as_JSONle': _t('Error: Could not update orders'),
                            'body': _t('Your connection is probably down.'),
                        });
                    });
                }
            }
            this._super(line, event);
        },
        update_orderlines_stages: function(){
            var orderlines = this.pos.get_order().get_orderlines();
            var model = new Model('pos.work.order');
            var order_ids = []
            var self = this;
            for(var i=0; i<orderlines.length; i++){
                if(orderlines[i].get_work_order_id()){
                    order_ids.push(orderlines[i].get_work_order_id());
                }
            }
            if (order_ids.length){
                model.call('get_stage_from_ui',[order_ids]).then(function(orders_stage){
                    for(var i=0; i<orderlines.length; i++){
                        if(orders_stage[orderlines[i].work_order_id]){
                            orderlines[i].set_work_order_stage(orders_stage[orderlines[i].work_order_id]);
                        }
                    }
                },function(err,event){
                    event.preventDefault();
                    self.pos.gui.show_popup('error',{
                        'titexport_as_JSONle': _t('Error: Could not update orders'),
                        'body': _t('Your connection is probably down.'),
                    });
                });
            }

        },
        remove_orderline: function(order_line){
            this._super(order_line);
            if(order_line.get_work_order_id()){
                this.deleted_work_orders.push(order_line.get_work_order_id());
            }
        },
        sync: function(){
            var model = new Model('pos.work.order');
            var self = this;
            var orderlines = this.pos.get_order().get_orderlines();
            var fields = [];
            for(var i=0; i<orderlines.length; i++){
                if (orderlines[i].printable()){
                    fields.push(orderlines[i].get_fields_values());
                }
            }
            if (fields.length){
                model.call('create_from_ui',[fields]).then(function(work_orders){
                    for(var i=0; i<orderlines.length; i++){
                        var hash_str = orderlines[i].get_hash_str();
                        if (work_orders[hash_str]){
                            orderlines[i].set_work_order_stage(work_orders[hash_str][1]);
                            orderlines[i].set_work_order_id(work_orders[hash_str][0]);
                        }
                    }
                },function(err,event){
                    event.preventDefault();
                    self.pos.gui.show_popup('error',{
                        'title': _t('Error: Could not Save Changes'),
                        'body': _t('Your connection is probably down.'),
                    });
                });
            }
            var field_list = [];
            for(var i=0; i<this.deleted_work_orders.length; i++){
                field_list.push({
                    'id':this.deleted_work_orders[i],
                    'hash_str':this.deleted_work_orders[i],
                    'stage_id':5
                });
            }
            if(field_list.length){
                model.call('create_from_ui',[field_list]);
            }
            this.deleted_work_orders = [];

        },
    });

    screens.ProductScreenWidget.include({
        start: function(){
            this._super();
            var self = this;

            // maybe this isn't the best way to get in,
            //  but its the only one I found
            var SubmitOrderButton = $('.order-submit');
            SubmitOrderButton.bind('click', function(){
                self.order_widget.sync();
            });

        },
        show: function(){
            var self = this;
            this._super();
            this.order_widget.update_orderlines_stages();
            this.poll_id = setInterval(function(){
                self.order_widget.update_orderlines_stages();
            }, 5000);
        },
        hide: function(){
            this._super();
            clearInterval(this.poll_id);
        },
    });

});