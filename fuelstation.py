from dataclasses import field
from random import random
from venv import create
from odoo import models,fields,api
from odoo.exceptions import ValidationError
from datetime import datetime

#  Central Update Authentication details
import xmlrpc.client

url = "https://centralstation.prisms.in"
db = "centralstation"
username = 'ghanshyam.zurange@prisms.in'
password = "ghanshyam2477"


# list update the record to central
def update_to_central(update_rec_dict,table_id):
    # Api Key "e78da6874f54ae18c3302d2e6b1003c06dd9ee3f"
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    ver= common.version()
    print(ver)

    uid = common.authenticate(db, username, password, {})
    print(uid)
    
    new_dict={'sub_station':1}
    update_rec_dict.update(new_dict)

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    acc=models.execute_kw(db, uid, password, table_id, 'check_access_rights', ['read'], {'raise_exception': False})
    print("access>>",acc)

    id = models.execute_kw(db, uid, password, table_id, 'create', [update_rec_dict])
    print("Updated to central portal >>> id =",id)

    return id



# To update price to central
def update_price_to_central(fuel_type,new_price):
    # Api Key "e78da6874f54ae18c3302d2e6b1003c06dd9ee3f"
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    ver= common.version()
    print(ver)

    uid = common.authenticate(db, username, password, {})
    print(uid)
    
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    acc=models.execute_kw(db, uid, password, 'central.data', 'check_access_rights', ['read'], {'raise_exception': False})
    print("access>>",acc)

    print("Fuel Type >>>>>>>", fuel_type)
    if fuel_type=="Petrol":
        id=1
    elif fuel_type=="Diesel":
        id=2
    elif fuel_type=="CNG":
        id=3
    # Update
    check=models.execute_kw(db, uid, password, 'central.data', 'write', [[id], {'price':new_price}])
    print(check)
    # get record name after having changed it
    check2= models.execute_kw(db, uid, password, 'central.data', 'name_get', [[id]])
    print(check2)

#  Update Stock in central station
def update_stock_to_central(fuel_type,stock_update):
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    ver= common.version()
    print(ver)

    uid = common.authenticate(db, username, password, {})
    print(uid)

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    acc=models.execute_kw(db, uid, password, 'central.data', 'check_access_rights', ['read'], {'raise_exception': False})
    print("access>>",acc)

    if fuel_type=="Petrol":
        id=1
    elif fuel_type=="Diesel":
        id=2
    elif fuel_type=="CNG":
        id=3
    # Update
    check=models.execute_kw(db, uid, password, 'central.data', 'write', [[id], {'fuel_qut': stock_update}])
    print(check)
    # get record name after having changed it
    check2= models.execute_kw(db, uid, password, 'central.data', 'name_get', [[id]])
    print(check2)

# Update tanker status
def update_tanker_status_to_center(id):
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    ver= common.version()
    print(ver)

    uid = common.authenticate(db, username, password, {})
    print(uid)
    
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    print("id is --------",id)
    acc=models.execute_kw(db, uid, password, 'central.tanker', 'check_access_rights', ['read'], {'raise_exception': False})
    print("access>>",acc)
    

    check=models.execute_kw(db, uid, password, 'central.tanker', 'write', [[id], {'status':'delivered'}])
    print(check) # return true
    return check

# Models
class FuelStation_in_stock(models.Model):
    _name= "fuelstation.instock"
    _description ="IN Fuel Record"
    name = fields.Char("Recived By")
    date = fields.Datetime("Date", default=datetime.today())
    fuel_type = fields.Many2one(comodel_name ="fuelstation.fueldata",string="Fuel Type") 
    instock_qut= fields.Float("IN stock Quantity")
    tanker_rec_id=fields.Integer("Tanker Record Id")

    # To Update the stock & update data in central portal
    sub_station=fields.Integer('Central DB Id')
    @api.model
    def create(self, vals_list):
        res=super(FuelStation_in_stock,self).create(vals_list)
        res.fuel_type.avl_qut += res.instock_qut # to add stock
        update_stock_to_central(res.fuel_type.name,res.fuel_type.avl_qut)
        print("Val>>>> ", vals_list)
        central_id=update_to_central(vals_list,"central.transaction_in")
        print("retuned Central id =====", central_id)
        res.sub_station= central_id
        tanker_rec_check=update_tanker_status_to_center(res.tanker_rec_id)
        print("Tanker Update Status........",tanker_rec_check)
        return res



class FuelStation_out_stock(models.Model):
    _name="fuelstation.outstock"
    _description ="OUT Fuel Record"
    name = fields.Char("Customer Name")
    date = fields.Datetime("Date",default=datetime.today())
    fuel_type = fields.Many2one(comodel_name ="fuelstation.fueldata",string="Fuel Type")
    order_qut= fields.Float("Fuel Quantity in Ltrs")
    fuel_price= fields.Float(string="Current Fuel Price",related='fuel_type.price') 
    avl_qut = fields.Float(string="Available Fuel",related='fuel_type.avl_qut')

    # Store current price
    @api.depends('fuel_type')
    def _price_store(self):
        for rec in self:
            temp_price=rec.fuel_price
        self.price=temp_price
        
    price= fields.Float(string="Fuel Price On Order",compute=_price_store,store=True,readonly=False)



    #  for Total price
    @api.depends('fuel_type','order_qut')
    def _cal_total(self):
        for rec in self:
            rec.total_price= rec.order_qut* rec.fuel_price
        self.total_price= rec.total_price

    total_price = fields.Float(string="Total Cost",compute=_cal_total,store=True,readonly=False)

    # To Update stock
    @api.depends('order_qut')
    def _update_stock(self):
        for rec in self:
            if rec.order_qut < rec.fuel_type.avl_qut: # to check out off stock condition
                rec.fuel_type.avl_qut -= rec.order_qut 
            else:
                raise ValidationError("Fuel Out off Stock")
        self.updated_stock= rec.fuel_type.avl_qut
        update_stock_to_central(rec.fuel_type.name,self.updated_stock)


    updated_stock= fields.Float(string="Updated Stock",compute=_update_stock,  store=True)



    val_list=None
    # Updated the record in central DataBase
    sub_station=fields.Integer('Central DB Id')
    @api.model
    def create(self, vals_list):
        print("Val List >>>>>>>",vals_list)
        central_id = update_to_central(vals_list,"central.transaction_out") # For update the record to central
        vals_list['sub_station']= central_id #here insted of 12 to update field
        # update_to_central(vals_list,"central.transaction_out")
        # print("Returned>>>",central_id) 
        # self.val_list= vals_list
        return super().create(vals_list)
        
    # to update failed record

    # @api.model
    # def write(self, vals):
    #     central_id= update_to_central(vals,"central.transaction_out")
    #     vals['sub_station']= central_id
    #     return super().write(vals)

    def update_central_bt(self):
        print(self.val_list)
        update_to_central(self.val_list,"central.transaction_out")
        print("Button Clicked!!!!!!!!!!!!!!!!")

class FuelStation_fuel_data(models.Model):
    _name="fuelstation.fueldata"
    name= fields.Char(string= "Fuel Type")
    price= fields.Float(string="Fuel Price")
    avl_qut= fields.Float(" Available Fuel")


class FuelStation_transaction_rec(models.Model):
    _name="fuelstation.record"
    name=fields.Char(string="IN/OUT")
    date = fields.Datetime("Date")
    fuel_type = fields.Many2one(comodel_name ="fuelstation.fueldata",string="Fuel Type")
    order_qut= fields.Float("Fuel Quantity in Ltrs")
    fuel_price= fields.Float(string="Fuel Price",related='fuel_type.price')



class FuelStation_fuel_price(models.Model):
    _name= "fuelstation.fuelprice"
    name= fields.Char(string= "Fuel Type")
    fuel_type = fields.Many2one(comodel_name ="fuelstation.fueldata",string="Fuel Type")
    fuel_price= fields.Float(string="Fuel Price",related='fuel_type.price',readonly=False)

    # To update price in central portal
    def write(self, vals):
        print("fuel Type is.....",self.fuel_type.name)
        print("vals after updating.........",vals['fuel_price']) # this value will pass as new_price
        update_price_to_central(self.fuel_type.name,vals['fuel_price'])
        return super().write(vals) 


class FuelStation_avl_stock(models.Model):
    _name= "fuelstation.avlstock"
    name= fields.Char(string= "Fuel Type")
    fuel_type = fields.Many2one(comodel_name ="fuelstation.fueldata",string="Fuel Type")
    avl_qut = fields.Float(string="Fuel Quantity in Ltrs",related='fuel_type.avl_qut',readonly=False, store=True)

    def write(self, vals):
        print("avilable qut.......",vals)
        return super().write(vals)