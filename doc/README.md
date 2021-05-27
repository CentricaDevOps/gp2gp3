# GP2 to GP3 Transition

Automatically transition gp2 EBS volumes to gp3 as they appear in an account.

As various features of AWS like Launch Templates, most instance definitions etc,
have hard coded references to gp2 type volumes this process will be required to
run continuously until all those references are updated to gp3. It is designed
to run currently on a 15 minute schedule.

On December 1st, 2020 AWS announced the availability of gp3, the next generation
of General Purpose SSD (Solid State Drive) Volumes for Amazon Elastic Block
Store (AWS EBS).

This volume type offers significant throughput enhancement and cost benefits
over the existing gp2 type.  With gp2, to obtain faster throughput you had to
provision larger volume sizes, this is no longer necessary with gp3.  Also, gp3
offers an instant 20% cost saving over the equivalent sized gp2 volume.

## Architecture

As we manage a lot of individual AWS Accounts, under a few Account
Organisations, with upto 16 regions being available in each of those accounts a
parallel processing method will be employed to collect information about the
Volumes. This will be a Director => Worker architecture, with one Worker per
account starting a thread per region in that account.

See [Director Lambda](director.md) for an overview of this architecture.

Essentially, each account and region in that account will autonomously manage
the migration of it's Volumes from gp2 to gp3, without reference to other
regions or accounts.

This architecture is both efficient, fast and light on resources.

## Testing

Amazon made great play of not only the full availability of gp3 but also the
seamless migration path from gp2 to gp3.  I decided to test this on a number of
volumes in various states.

Using the console I first migrated a 500GB 20% used volume that was currently
not in use.  The process took about 2 minutes and worked flawlessly.  I then
attached a brand new gp2 volume to a running EC2 instance and hit the modify
volume button again.  Once again, no issues to report.  OK, lets stress test it.

I created another, new 200GB volume, attached it to an m5 instance, set off a
constant read in one terminal, a constant write in another and then hit the
migration switch - I couldn't detect any performance hit at all, though this
time the modification process took ~11 minutes.

## The Code

See [Code Breakdown](code.md) for the full, unexpurgated details.
