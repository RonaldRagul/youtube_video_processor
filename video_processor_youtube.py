import os
from pytube import YouTube
import pandas as pd
from moviepy.editor import *
import getopt
import sys

def main(argv):
    csv_input = ''
    head_path = ''
    tail_path = ''
    audio_input = ''
    logo_input_path = ''
    try:
       opts, args = getopt.getopt(argv,"i:h:t:a:l:",["csv_input=","head_path=","tail_path=","audio_input=","logo_input_path="])
    except getopt.GetoptError:
       print('Usage: python video_processor.py -i <csv_input> -h <head_path> -t <tail_path> -a <audio_input> -l <logo_input_path>')
       sys.exit(2)

    csv_input, head_path, tail_path, audio_input, logo_input_path = None, None, None, None, None


    for opt, arg in opts:
       if opt == '-i': 
          csv_input = arg
       elif opt == '-h':
          head_path = arg
       elif opt == '-t':
          tail_path = arg
       elif opt == '-a':
          audio_input = arg
       elif opt == '-l':
          logo_input_path = arg

    if csv_input is None or head_path is None or tail_path is None or audio_input is None or logo_input_path is None:
        print('Usage: python video_processor.py -i <csv_input> -h <head_path> -t <tail_path> -a <audio_input> -l <logo_input_path>')
        sys.exit(2)


    # read the csv file into a pandas DataFrame
    df = pd.read_csv(csv_input)

    # create a new DataFrame to store print messages
    result_df = pd.DataFrame(columns=['Output Name', 'Message'])

    # create the download and combined folders if they don't already exist
    folder_names = ["download_folder", "combined_folder"]
    for folder_name in folder_names:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

    combined_folder = "combined_folder"
    download_folder  = "download_folder"

    # loop through each row in the DataFrame
    for index, row in df.iterrows():
        try:
            # create a YouTube object for the video you want to download
            yt = YouTube(row['URL'])

            # set up the output path and file name
            output_path = download_folder
            file_name = yt.title + ".mp4"
            video_file = os.path.join(output_path, file_name)

            # loop until the download is successful
            while True:
                try:
                    # get the stream with the highest resolution
                    stream = yt.streams.get_highest_resolution()
                    # download the video to the specified directory
                    video_file = stream.download(output_path=output_path, filename=file_name)
                    print(f"Downloaded {yt.title}")
                    break  # exit the loop if download is successful
                except Exception as e:
                    print(f"An error occurred while downloading {yt.title}: {e}")
                    print("Retrying...")

            # load the video clip
            video_clip = VideoFileClip(video_file)


            try:
              start_time_str = str(row["START"])  # format: MM:SS
              start_time = list(map(int, start_time_str.split(":")))
              start_seconds = start_time[0] * 60 + start_time[1]
            except ValueError:
              start_seconds = 0.0

            try:
              end_time_str = str(row["END"])  # format: MM:SS
              end_time = list(map(int, end_time_str.split(":")))
              end_seconds = end_time[0] * 60 + end_time[1]
            except ValueError:
              end_seconds = video_clip.duration
            if start_seconds is not None and end_seconds is not None:
            # check if the end trim value is greater than the video duration
              if start_seconds <= video_clip.duration:
            # trim the video
                video_clip = video_clip.subclip(start_seconds, end_seconds)
              else:
                print("End trim duration is longer than video duration.")
            else:
                print("No trim input provided.")

            # add audio if specified
            audio_insert = row['AUDIO_INSERT']
            if audio_insert == 'YES':
                audio_clip = AudioFileClip(audio_input)
                audio_clip = audio_clip.subclip(0, video_clip.duration)
                video_clip = video_clip.set_audio(audio_clip)
                print("Audio merged")


            # add logo if specified
            logo_position = row['LOGO_POSITION']
            if logo_position != '':
                logo_clip = ImageClip(logo_input_path)
                logo_clip = logo_clip.set_duration(video_clip.duration)
                logo_clip = logo_clip.set_position((logo_position.lower(), 'top'))
                video_clip = CompositeVideoClip([video_clip, logo_clip])
                print("Logo added")

            # load the header and tail clips
            header_clip = VideoFileClip(head_path)
            tail_clip = VideoFileClip(tail_path)
            while True:
                try:
                    # combine the clips
                    combined_clip = concatenate_videoclips([header_clip, video_clip, tail_clip])
                    break
                except Exception as e:
                    print(f"An error occurred while combining {yt.title}: {e}")
                    print("Retrying...")

                    # write the combined clip to file
                    output_name = row['OUTPUT']
                    output_path = f"{combined_folder}/{output_name}.mp4"
                    combined_clip.write_videofile(output_path)

                    # add success message to the result DataFrame
                    result_df = result_df.append(
                        {'Output Name': output_name, 'Message': f"Video '{yt.title}' combined successfully."},
                        ignore_index=True)


        except Exception as e:
           # add error message to the result DataFrame
           result_df = result_df.append({'Output Name': row['OUTPUT'], 'Message': f"Error combining video: {e}"}, ignore_index=True)

    # write the result DataFrame to file
    result_df.to_csv("result.csv", index=False)
    print("Result generated.")

if __name__ == "__main__":
    main(sys.argv[1:])