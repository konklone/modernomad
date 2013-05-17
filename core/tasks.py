from celery.task.schedules import crontab
from celery.task import periodic_task
from core.models import Reservation, UserProfile
from django.contrib.auth.models import User
import datetime
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import get_template
from django.template import Context
from django.core import urlresolvers
from django.core.mail import EmailMultiAlternatives

weekday_number_to_name = {
	0: "Monday",
	1: "Tuesday",
	2: "Wednesday",
	3: "Thursday",
	4: "Friday",
	5: "Saturday",
	6: "Sunday"
}


#@periodic_task(run_every=crontab(hour=22, minute=53, day_of_week="*"))  
#def test():      
#    print "HELLO WORLD"                    

@periodic_task(run_every=crontab(hour=4, minute=30))
# @periodic_task(run_every=crontab(minute="*")) # <-- for testing
def arriving_today():
	today = datetime.datetime.today() 
	arriving_today = Reservation.objects.filter(arrive=today).filter(status='confirmed')
	print "%d arriving today" % len(arriving_today)
	domain = Site.objects.get_current().domain
	plaintext = get_template('emails/arriving_today_notification.txt')
	c = Context({
		'reservations' : arriving_today,
		'domain': domain,
	})
	text_content = plaintext.render(c)
	subject = "[Embassy SF] Guest Arrivals for %s" % (str(today))
	sender = settings.DEFAULT_FROM_EMAIL
	# XXX this is a temporary hack until we make this a setting on the
	# house admin accounts. 
	recipients = ["chelseamangold@gmail.com", "jessy@jessykate.com", "derek.dunfield@gmail.com", "kris.tew@gmail.com"]
	msg = EmailMultiAlternatives(subject, text_content, sender, recipients)
	msg.send()

@periodic_task(run_every=crontab(hour=2, minute=0))
def guest_welcome():
	# get all reservations arriving tomorrow (day = today + 1)
	tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
	upcoming = Reservation.objects.filter(arrive=tomorrow).filter(status='confirmed')
	domain = Site.objects.get_current().domain
	plaintext = get_template('emails/pre_arrival_welcome.txt')
	day_of_week = weekday_number_to_name[datetime.datetime.today().weekday()]
	for reservation in upcoming:
		c = Context({
			'first_name': reservation.user.first_name,
			'day_of_week' : day_of_week,
			'site_url': domain,
			'events_url' : "http://facebook.com/embassynetwork/events",
			'profile_url' : "https://" + domain + urlresolvers.reverse('user_details', args=(reservation.user.id,)),
			'reservation_url' : "https://" + domain + urlresolvers.reverse('reservation_detail', args=(reservation.id,)),
		})
		text_content = plaintext.render(c)
		subject = "[Embassy SF] Your stay from %s - %s" % (reservation.arrive, reservation.depart)
		sender = settings.DEFAULT_FROM_EMAIL
		recipients = [reservation.user.email,]
		msg = EmailMultiAlternatives(subject, text_content, sender, recipients)
		msg.send()

