import sys, argparse, logging, os
import json
import couchdb
import math


def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)
  
  # TODO Replace this with your actual code.
    couch = couchdb.Server('http://elferich:particles@localhost:5984/')

    with open("/hotspur/scratch/"+args.user+"/"+args.dataset+"/data.json","r") as fp:
        data = json.load(fp)
    db = couch.create(args.user+"_"+args.dataset)

    for key in data:
        if "Gctf" in data[key]:
            doc = {}
            doc['_id'] = key+"_ctf_datajsonimport"
            doc['micrograph'] = key
            doc['type'] = "ctf"
            doc['program'] = "Gctf 1.06"

            doc['astigmatism_angle'] = data[key]['Gctf']['Astig angle']
            doc['defocus_u'] = data[key]['Gctf']['Defocus U']
            doc['defocus_v'] = data[key]['Gctf']['Defocus V']
            #doc['ctf_measured'] = data[key]['Gctf']['EPA']['Meas. CTF']
            #doc['ctf_measured_nobg'] = data[key]['Gctf']['EPA']['Meas. CTF - BG']
            #doc['ctf_resolution_a'] = data[key]['Gctf']['EPA']['Resolution']
            #doc['ctf_theory'] = data[key]['Gctf']['EPA']['Sim. CTF']
            doc['estimated_b_factor'] = data[key]['Gctf']['Estimated b-factor']
            doc['estimated_resolution'] = data[key]['Gctf']['Estimated resolution']
            doc['phase_shift'] = data[key]['Gctf']['Phase shift']
            doc['gctf_validation_scores'] = data[key]['Gctf']['Validation scores']
            doc['gctf_file_epa_log']  = data[key]['Gctf']['ctf_epa_log_filename']
            doc['file_ctf_image'] = data[key]['Gctf']['ctf_image_filename']
            doc['file_ctf_image_preview'] = data[key]['Gctf']['ctf_preview_image_filename']
            doc['file_ctf_star'] = data[key]['Gctf']['ctf_star_filename']
            doc['file_ctf_log'] = data[key]['Gctf']['ctf_log_filename']
            db.save(doc)
        if "MotionCor2" in data[key]:
            doc = {}
            doc['_id'] = key+"_motioncorrection_datajsonimport"
            doc['micrograph'] = key
            doc['type'] = "motioncorrection"
            doc['program'] = "motioncor2 1.10"

            doc['dimensions'] = data[key]['MotionCor2']['dimensions']
            doc['file_dw'] = data[key]['MotionCor2']['dw_micrograph_filename']
            doc['file_sum'] = data[key]['MotionCor2']['sum_micrograph_filename']
            doc['file_log'] = data[key]['MotionCor2']['log_filename']
            doc['pixel_size'] = data[key]['MotionCor2']['pixel_size']
            doc['file_preview'] = data[key]['MotionCor2']['preview_filename']
            #doc['frame_shifts'] = [data[key]['MotionCor2']['x_shifts'],data[key]['MotionCor2']['y_shifts']]
            doc['initial_shift'] = math.sqrt(data[key]['MotionCor2']['x_shifts'][0]**2 + data[key]['MotionCor2']['y_shifts'][0]**2)
            total = 0
            for i,a in enumerate(data[key]['MotionCor2']['x_shifts']):
                total += math.sqrt(a**2 + data[key]['MotionCor2']['y_shifts'][i]**2)
            doc['total_shift'] = total
            db.save(doc)
        if "idogpicker" in data[key]:
            doc = {}
            doc['_id'] = key+"_particles_datajsonimport"
            doc['micrograph'] = key
            doc['type'] = "particles"
            doc['program'] = "idogpicker"

            doc['idogpicker_file'] = data[key]["idogpicker"]["idogpicker_filename"]
            db.save(doc)

        if "moviestack" in data[key]:
            doc = {}
            doc['_id'] = key+"_movie_datajsonimport"
            doc['micrograph'] = key
            doc['type'] = "movie"

            doc['acquisition_time'] = data[key]['moviestack']['acquisition_time']
            doc['dimensions'] = data[key]['moviestack']['dimensions']
            doc['number_frames'] = data[key]['moviestack']['numframes']
            doc['pixel_size'] = 0
            doc['dose_pixel_frame'] = data[key]['moviestack']['dose_per_pix_frame']
            doc['file'] = data[key]['moviestack']['filename']
            db.save(doc)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
                                        description = "This tool converts data.json file into a database in CouchDB",
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter

                                         )
      # TODO Specify your real parameters here.
    parser.add_argument(
                          "--user",
                          help = "User",
                          )
    parser.add_argument(
                          "--dataset",
                          help = "Dataset",
                          )
    parser.add_argument(
                          "-v",
                          "--verbose",
                          help="increase output verbosity",
                          action="store_true")
    args = parser.parse_args()
      
      # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    main(args, loglevel)
