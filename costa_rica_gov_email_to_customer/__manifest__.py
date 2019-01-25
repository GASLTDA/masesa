{
    'name' : '(Email) Costa Rica Government Submission of invoice',
    'version' : '1.1',
    'author' : 'Janeindiran',
    'summary': 'Send Invoices and Track Payments',
    'sequence': 30,
    'description': """Text file to submit invoice information""",
    'category': 'Accounting',
    'depends' : ['base','base_setup', 'account','costa_rica_gov_submission'],
    'installable': True,
    'website': 'https://janeindiran.com',
    'application': False,
    'auto_install': False,
    'data': [
         'data/scheduler.xml',
        'views/account_invoice.xml'
    ],
    'post_init_hook': '_auto_install_data',

}
