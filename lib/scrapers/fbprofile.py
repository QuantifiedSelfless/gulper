from tornado import gen

from facebook import GraphAPI

class FBProfileScraper(object):
    name = 'fbprofile'

    @gen.coroutine
    def scrape(self, user_data):
        try:
            oauth = user_data.services['facebook']['access_token']
        except KeyError:
            return False
        graph = GraphAPI(access_token=oauth)
        print("[fbprofile] Scraping user: ", user_data.userid)

        profile = graph.get_object('me', 
            fields = 'bio, birthday, education, interested_in, hometown, political, relationship_status, religion, work')

        data = {}

        data['birthday'] = profile.get('birthday', None)
        data['bio'] = profile.get('bio', None)
        if 'education' in profile:
            data['education'] = []
            for sch in profile['education']:
                school = {}
                try:
                    school['name'] = sch.get('name', None)
                    school['degree'] = sch.get('degree', None)
                except KeyError:
                    print('error in FB education info')
                    continue
                data['education'].append(school)
        data['sex_preference'] = profile.get('interested_in', None)
        if 'hometown' in profile:
            data['homtown'] = profile['hometown']['name']
        data['political'] = profile.get('political', None)
        data['relationship_status'] = profile.get('relationship_status', None)
        data['religion'] = profile.get('religion', None)
        if 'work' in profile:
            data['work'] = []
            for job in profile['work']:
                emp = {}
                try:
                    emp['name'] = job['employer'].get('name', None)
                    emp['position'] = job['position'].get('name', None)
                    emp['location'] = job['location'].get('name', None)
                except KeyError:
                    print('error in FB work info')
                    continue
                data['work'].append(emp)
        return data