import torch.nn as nn
import torch
import numpy as np
NUM_CLASSES = 3
DATA_LENGTH = 128
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Critic(nn.Module):
    def __init__(self, channels_img, features_d, num_classes, img_size):
        super().__init__()
        self.img_size = img_size
        self.laten_num = 97
        self.norm = nn.BatchNorm1d(self.laten_num+NUM_CLASSES)
        self.disc = nn.Sequential(
            # input : N * channels_img * 64 * 64
            # nn.Conv2d(channels_img+1, features_d, kernel_size=4, stride=2, padding=1),
            nn.Conv2d(channels_img, features_d, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            # _block(in_channels, out_channels, kernel_size, stride, padding)
            self._block(features_d, features_d*2, 4, 2, 1),
            self._block(features_d*2, features_d*4, 4, 2, 1),
            self._block(features_d*4, features_d*8, 4, 2, 1),
            # After all _block img output is 4x4 (Conv2d below makes into 1x1)
            nn.Conv2d(features_d*8, self.laten_num+NUM_CLASSES, kernel_size=4, stride=2, padding=0),
            nn.Dropout(0.5),
            nn.Flatten(),
            nn.Tanh()
        )
        self.tanh = nn.ReLU()
        self.embed = nn.Embedding(num_classes, img_size*img_size)
        self.imagine_num = int((self.laten_num+NUM_CLASSES)/2)
        self.layerX = nn.Sequential(nn.Linear(self.imagine_num, int(self.imagine_num/2)),nn.Linear(int(self.imagine_num/2), self.imagine_num),nn.ReLU(), nn.Dropout(0.5))
        self.layerY = nn.Sequential(nn.Linear(self.imagine_num, int(self.imagine_num/2)),nn.Linear(int(self.imagine_num/2), self.imagine_num),nn.ReLU(), nn.Dropout(0.5))
        self.fully_layer = nn.Sequential(nn.Linear(self.imagine_num*2, int(self.imagine_num/2)),nn.Linear(int(self.imagine_num/2),self.imagine_num),nn.Dropout(0.5), nn.Sigmoid()) # , nn.Tanh()


    def _block(self, in_channels, out_channels, kernel_size, stride, padding):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias = True,),
            # nn.Dropout2d(0.5),
        nn.InstanceNorm2d(out_channels, affine=True),
        nn.LeakyReLU(0.2),
        )

    def _imagine1(self,imagin_flatten_data):
      x = imagin_flatten_data[:,:self.imagine_num]
      y = imagin_flatten_data[:,self.imagine_num:]
      xx = self.tanh(self.layerX(x)-self.layerY(y))
      yy = self.tanh(self.layerX(y)+self.layerY(y))      
      return torch.cat([xx,yy], dim=1)    
    
    def forward(self, x):
       
        x = self.disc(x)
        x = self.norm(x)
        x =self._imagine1(x)
        x =self.fully_layer(x)
        return x

class Critic_128(nn.Module):
    def __init__(self, channels_img=128, features_d=16, num_classes=3, img_size=128):
        super().__init__()
        self.img_size = img_size
        self.laten_num = 97
        self.disc = nn.Sequential(
            # input : N * channels_img * 64 * 64
            # nn.Conv2d(channels_img+1, features_d, kernel_size=4, stride=2, padding=1),
            nn.Conv2d(channels_img, features_d, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            # _block(in_channels, out_channels, kernel_size, stride, padding)
            self._block(features_d, features_d*2, 4, 2, 1),
            self._block(features_d*2, features_d*4, 4, 2, 1),
            self._block(features_d*4, features_d*8, 4, 2, 1),
            # After all _block img output is 4x4 (Conv2d below makes into 1x1)
            nn.Conv2d(features_d*8, self.laten_num+NUM_CLASSES, kernel_size=4, stride=2, padding=0),
            nn.Dropout(0.5),
            nn.Flatten(),
            nn.Tanh()
        )
        self.tanh = nn.ReLU()
        self.embed = nn.Embedding(num_classes, img_size*img_size)

        # self.imagine_num = int((self.laten_num+NUM_CLASSES)/2) 
        self.imagine_num = int(900/2) 
        self.norm = nn.BatchNorm1d(900)

        self.layerX = nn.Sequential(nn.Linear(self.imagine_num, int(self.imagine_num/2)),nn.Linear(int(self.imagine_num/2), self.imagine_num),nn.ReLU(), nn.Dropout(0.5))
        self.layerY = nn.Sequential(nn.Linear(self.imagine_num, int(self.imagine_num/2)),nn.Linear(int(self.imagine_num/2), self.imagine_num),nn.ReLU(), nn.Dropout(0.5))
        self.fully_layer = nn.Sequential(nn.Linear(self.imagine_num*2, int(self.imagine_num/2)),nn.Linear(int(self.imagine_num/2),self.imagine_num),nn.Dropout(0.5), nn.Sigmoid()) # , nn.Tanh()

        # self.norm = nn.BatchNorm1d(self.laten_num+NUM_CLASSES)

    def _block(self, in_channels, out_channels, kernel_size, stride, padding):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding, bias = True,),
            # nn.Dropout2d(0.5),
        nn.InstanceNorm2d(out_channels, affine=True),
        nn.LeakyReLU(0.2),
        )

    def _imagine1(self,imagin_flatten_data):
      x = imagin_flatten_data[:,:self.imagine_num]
      y = imagin_flatten_data[:,self.imagine_num:]
      xx = self.tanh(self.layerX(x)-self.layerY(y))
      yy = self.tanh(self.layerX(y)+self.layerY(y))      
      return torch.cat([xx,yy], dim=1)    
    # def _imagine2(self,imagin_flatten_data):
    #   x = imagin_flatten_data[:,:self.imagine_num]
    #   y = imagin_flatten_data[:,self.imagine_num:]
    #   xx = self.tanh(self.layerX(x)-self.layerY(y))
    #   yy = self.tanh(self.layerX(y)+self.layerY(y))      
    #   return torch.cat([xx,yy], dim=1)    
    # def _imagine3(self,imagin_flatten_data):
    #   x = imagin_flatten_data[:,:self.imagine_num]
    #   y = imagin_flatten_data[:,self.imagine_num:]
    #   xx = self.tanh(self.layerX(x)-self.layerY(y))
    #   yy = self.tanh(self.layerX(y)+self.layerY(y))      
    #   return torch.cat([xx,yy], dim=1)
    def forward(self, x):
        # embedding = self.embed(labels).view(labels.shape[0], 1, self.img_size, self.img_size)
        # x = torch.cat([x, embedding], dim=1) # N x C x img_size(H) x img_size(W)
        x = self.disc(x)
        x = self.norm(x)
        # x =self._imagine1(x)
        x =self.fully_layer(x)
        return x

class Code_obj:
    def __init__(self):
        self.last_data = None
        self.model = None
        self.data = None

    def forward(self):
        self.model.eval()
        data = self._preprocess_img(self.data).to(DEVICE)
        ret = self.model(data.float())
        res = ret[0][-3:]      
        action = torch.argmax(res)
        rate = res[action]
        # print(res.argmax())
        return action, rate

    def _preprocess_img(self, data):        
        data = np.array(data)
        img_units = list()
        for i in range(5):
            # print(i)
            # print(data)
            col_data = data[:,i]
            col_data = normalize_custom(col_data)
            col_data = np.squeeze(col_data, axis=-1)
            img = making_img(col_data)
            img_units.append(np.expand_dims(img, axis=0))
        data_unit = np.concatenate(img_units)
        data_unit = torch.from_numpy(data_unit)
        data_unit = torch.unsqueeze(data_unit, axis=0)
        return data_unit

    def update(self, new_data):
        self.data.append(new_data)
        self.last_data = new_data
        del(self.data[0])
        return self.data
    
    def check(self, new_data):
        if self.last_data == new_data:
            return True
        return False

def read_company_codes():
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWORD, host=HOST, port="5432")
    cur = conn.cursor()
    sql = 'SELECT company_code FROM company_codes_trade;'
    cur.execute(sql)
    res = cur.fetchall()    
    conn.commit()
    cur.close()
    conn.close()
    return res
  
def split_contents(df):
    return df[0]

def normalize_custom(X, type=0):
    X = np.array(X, dtype=float)
    X = np.abs(X)
    # X = np.log(X)
    X = np.expand_dims(X, axis=1)
    # 정규화 3가지 방식
    # 1. X-m/max-min
    # 2. X-m/sd
    # 3. 2*(X-m/max-min)-1    
    max = X.max()
    min = X.min()
    sd = X.std()
    mean = X.mean()
    def func0():
        return (X-min)/(max-min+1)
    def func1():
        return (X-mean)/sd
    def func2():
        return 2*(X-min)/(max-min)-1
    func_list=[func0, func1, func2]
    return func_list[type]()
    
def normalize_custom(X, type=0):
    X = np.array(X, dtype=float)
    X = np.abs(X)
    # X = np.log(X)
    X = np.expand_dims(X, axis=1)
    # 정규화 3가지 방식
    # 1. X-m/max-min
    # 2. X-m/sd
    # 3. 2*(X-m/max-min)-1    
    max = X.max()
    min = X.min()
    sd = X.std()
    mean = X.mean()
    def func0():
        return (X-min)/(max-min+1)
    def func1():
        return (X-mean)/sd
    def func2():
        return 2*(X-min)/(max-min)-1
    func_list=[func0, func1, func2]
    return func_list[type]()
    
def making_img(col_datas, width=DATA_LENGTH, height=DATA_LENGTH):
    img = torch.zeros((height,width))
    max , min = 1.0, 0.0
    for i, price in enumerate(col_datas):
        
            y = int(
            (1-(price-min)/(max-min))*(height-1)
            )
            img[y,i] = 1.0
                    
        # print(y)
    # plt.imshow(img, cmap="gray")
    # plt.show()
    return img
