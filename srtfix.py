# -*- coding: utf-8 -*-
from datetime import datetime
import getopt, re, sys

count = 0
def fix_srt(inputfile):
  global count
  parsed_file, errors_file = '', ''
  try:
    with open( inputfile , 'r') as f:
      srt_file = f.read()
      parsed_file, errors_file = parse_srt(srt_file)
  except:
    pass
  finally:
    outputfile1 = ''.join( inputfile.split('.')[:-1] ) + '_fixed.srt'
    outputfile2 = ''.join( inputfile.split('.')[:-1] ) + '_error.srt'
    with open( outputfile1 , 'w') as f:
      f.write(parsed_file)
    with open( outputfile2 , 'w') as f:
      f.write(errors_file)
    print('Detected %s errors in "%s". Fixed file saved as "%s" (Errors only as "%s").' % ( count, inputfile, outputfile1, outputfile2 ))

previous_end_time = datetime.strptime("00:00:00,000", "%H:%M:%S,%f")
def parse_times(times):
  global previous_end_time
  global count
  _error = False
  _times = []
  for time_code in times:
    t = datetime.strptime(time_code, "%H:%M:%S,%f")
    _times.append(t)

  if _times[0] < previous_end_time:
    _times[0] = previous_end_time
    count += 1
    _error = True
  previous_end_time = _times[1]

  _times[0] =  _times[0].strftime("%H:%M:%S,%f")[:12]
  _times[1] = _times[1].strftime("%H:%M:%S,%f")[:12]

  return [_times, _error]

def parse_srt(srt_file):
  global count
  parsed_srt = []
  parsed_err = []
  all_captions = []
  all_lines = re.sub('\r\n', '\n', srt_file).split('\n\n')
  for idx, srt_group in enumerate(all_lines):
    lines = srt_group.split('\n')
    if len(lines) >= 3:
      times = lines[1].split(' --> ')
    all_captions.append({
      "times": times,
      "text": ""
    })
#   print(all_captions)
  for idx, srt_group in enumerate(all_lines):
    # print(f"idx: {idx}")
    # print(all_captions[idx].get('times'))
    lines = srt_group.split('\n')
    if len(lines) >= 3:
      times = lines[1].split(' --> ')
    # print(times)
    # print(len(times))
    if len(times) < 2:
      print(f"XXX Times length Error at: {lines}")
      print(f"XXX at times: {times}")
      error = True
      count += 1
      try:
        border_time_before = all_captions[idx - 1]['times'][1]
      except:
        border_time_before = ''
      try:
        border_time_after = all_captions[idx + 1]['times'][0]
      except:
        border_time_after = ''
      border_times = [border_time_before, border_time_after]
    #   print(f"border_times: {border_times}")
      correct_times = [
        times[0] if len(times) > 0 else border_time_before,
        times[1] if len(times) > 1 else border_time_after
      ]
    else:
        [correct_times, error] = parse_times(times)
    # print(error)
    # print(correct_times)
    if error:
    #   print(error)
      print(f"XXX Error ({count}) at: {times}")
      print(f"XXX Corrected: {correct_times}")
      clean_text = map( lambda x: x.strip(' '), lines[2:] )
      srt_group = lines[0].strip(' ') + '\n' + ' --> '.join( correct_times ) + '\n' + '\n'.join( clean_text )
      parsed_err.append( srt_group )
    # print(srt_group)
    parsed_srt.append( srt_group )
#   print(parsed_srt)
#   print(parsed_err)
  return '\r\n\r\n'.join( parsed_srt ), '\r\n\r\n'.join( parsed_err )

def main(argv):
  inputfile = None
  try:
    options, arguments = getopt.getopt(argv, "hi:", ["input="])
  except:
    print('Usage: test.py -i <input file>')

  for o, a in options:
    if o == '-h':
      print('Usage: test.py -i <input file>')
      sys.exit()
    elif o in ['-i', '--input']:
      inputfile = a
  fix_srt(inputfile)

if __name__ == '__main__':
  main( sys.argv[1:] )
