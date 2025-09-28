class UrlService:

    def __init__(self, db):
        self.db

    def get_urls_list(self):
        query = '''
            SELECT 
                u.id, 
                u.name, 
                MAX(uc.created_at) as last_check_date,
                (SELECT status_code 
                 FROM url_checks 
                 WHERE url_id = u.id 
                 ORDER BY created_at DESC 
                 LIMIT 1) as last_status_code
            FROM urls u
            LEFT JOIN url_checks uc ON u.id = uc.url_id
            GROUP BY u.id, u.name
            ORDER BY u.id DESC;
        '''
        urls = self.fetch_all(query)
        return urls
    
    def get_name_by_id(self, id):
        query = '''
            SELECT name 
            FROM urls 
            WHERE id = %s;'''
        name = self.fetch_one(query, (id,))
        return name
    
    def get_all_by_id(self, id):
        query = 'SELECT * FROM urls WHERE id = %s;'
        url_all = self.fetch_one(query, (id,))
        return url_all
    
    def get_id_by_name(self, name):
        query = 'SELECT id FROM urls WHERE name =%s;'
        url_id = self.fetch_one(query, (name,))
        return url_id
    
    def insert_name_time(self, name, time):
        query = '''
                    INSERT INTO urls(name, created_at) 
                    VALUES (%s, %s) RETURNING id;
                    '''
        posted_url = self.fetch_one(query, (name, time))[0]
        return posted_url
    
    def get_all_by_id_ordered(self, id):
        query = '''
        SELECT * FROM url_checks 
        WHERE url_id = %s 
        ORDER BY created_at DESC;
        '''
        ordered = self.fetch_all(query, (id,))
        return ordered
    
    def insert_url_checks(self, id, status, h1, title, descr, time):
        query = '''
        INSERT INTO 
        url_checks 
            (url_id, status_code, h1, title, description, created_at)
        VALUES (%s, %s, %s, %s, %s, %s);
        '''
        self.execute(query, (id, status, h1, title, descr, time))

    def insert_error(self, id, time):
        query = '''
            INSERT INTO url_checks (url_id, status_code, created_at)
            VALUES (%s, %s, %s);
        '''
        self.execute(query, (id, 0, time))
    



    
    
    

