import pyxel
import math

class WalkGame:
    def __init__(self):
        pyxel.init(160, 120)
        
        self.pet_width = 12
        self.pet_height = 12
        self.pet_x = 80
        self.pet_y = 100
        self.pet_vx = 2.0
        self.pet_speed = 2.0
        self.pet_speed_fast = 4.0
        
        self.lane_centers = [35, 75, 115]
        self.left_wall = 20
        self.right_wall = 130
        self.lane_width = 40
        
        self.poop_gauge = 0
        self.stamina_gauge = 100
        self.obstacles = []
        self.trash_bags = []
        self.speed = 1.0
        self.speed_increase = 0.005
        self.max_speed = 4.0
        self.game_over = False
        self.game_over_reason = ""
        self.min_spawn_distance = 40  # 最小距離を40に増加
        self.score = 0  # スコアを追加
        self.base_poop_increase = 0.1    # 基本増加量
        self.poop_speed_multiplier = 1.0 # 増加速度の倍率
        self.poop_acceleration = 0.005  # 倍率の増加速度
        
        # ゴミ袋の回復効果関連の変数を追加
        self.base_heal_amount = 10      # 基本回復量
        self.heal_multiplier = 1.0      # 回復効果の倍率
        self.heal_acceleration = 0.001   # 倍率の増加速度
        
        # 昼夜サイクル関連の変数を修正
        self.day_cycle = 0      # 0-1の値で時間を表現（0:昼、0.5:夜）
        self.day_speed = 0.002  # 初期値（update内で変更される）
        self.night_speed = 0.002  # 初期値（update内で変更される）
        self.is_darkening = True # True:暗くなる、False:明るくなる
        self.warning_threshold = 0.4  # 警告を表示開始する閾値
        
        # パワーアップアイテム関連
        self.power_items = []  # アイテムリスト [x, y, speed]
        self.has_power = False
        self.power_timer = 0
        self.power_duration = 180  # 3秒間（60FPS × 3）に変更
        self.bullets = []
        self.reload_timer = 0
        self.reload_time = 10

        self.has_flashlight = False
        self.fl_timer = 0
        self.flashlight_duration = 250  # 5秒間
        self.flashlight_items = [] 
        
        
        # ゴールまでの進行度関連
        self.progress = 0
        self.max_progress = 500  # ゴールまでの距離
        self.is_cleared = False   # クリアフラグ
        
        self.game_started = False  # スタート画面フラグ
        self.title_pet_rotation = 0  # タイトル画面での犬の回転角度
        
        self.clear_door_y = -50  # ドアの初期Y位置
        self.door_state = 0      # 0: 降下中, 1: 停止, 2: 開扉中, 3: 開, 4: 閉扉中, 5: 完了
        self.door_open_width = 0 # ドアの開き具合
        self.clear_timer = 0     # クリアアニメーションのタイミング用
        self.show_clear_screen = False # クリア画面表示フラグ
        self.poop_list = []  # うんちのリスト

        pyxel.run(self.update, self.draw)

    def is_space_clear(self, x, y):
        # 同じレーンと隣接レーンもチェック
        for obstacle in self.obstacles:
            if abs(obstacle[0] - x) <= 40 and abs(obstacle[1] - y) < self.min_spawn_distance:
                return False
                
        for trash in self.trash_bags:
            if abs(trash[0] - x) <= 40 and abs(trash[1] - y) < self.min_spawn_distance:
                return False
        for item in self.power_items:
            if abs(item[0] - x) <= 40 and abs(item[1] - y) < self.min_spawn_distance:
                return False
        for light in self.flashlight_items:
            if abs(light[0] - x) <= 40 and abs(light[1] - y) < self.min_spawn_distance:
                return False
        
        return True

    def update(self):
        if not self.game_started:
            # スタート画面での犬の回転アニメーション
            self.title_pet_rotation = (self.title_pet_rotation + 1) % 32  # 32フレームで1周
            if pyxel.btnp(pyxel.KEY_S):
                self.game_started = True
            return
        
        if self.game_over:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
            return
        
        if self.show_clear_screen:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
            if pyxel.btnp(pyxel.KEY_P):
            # ランダムな位置とサイズを生成
                poop_size = pyxel.rndi(3, 6)  # サイズを3から5の範囲でランダム
                poop_x = pyxel.rndi(0, pyxel.width - poop_size)
                poop_y = pyxel.rndi(0, pyxel.height - poop_size)
                self.poop_list.append((poop_x, poop_y, poop_size))  # うんちをリストに追加

            return
        
        if self.is_cleared:
            # クリア時に全てのオブジェクトを消去
            self.obstacles = []
            self.trash_bags = []
            self.power_items = []
            self.flashlight_items = []
            
            self.clear_timer += 1
            
            # ドアの降下アニメーション
            if self.door_state == 0:
                self.clear_door_y += 1
                if self.clear_door_y >= pyxel.height // 2 - 30:
                    self.door_state = 1
                    self.clear_timer = 0
            
            # ドアの停止
            elif self.door_state == 1 and self.clear_timer > 30:
                self.door_state = 2
            
            # ドアの開扉
            elif self.door_state == 2:
                self.door_open_width = min(20, self.door_open_width + 1)
                if self.door_open_width >= 20:
                    self.door_state = 3
                    self.clear_timer = 0
            
            # 犬がドアに向かって移動
            elif self.door_state == 3:
                target_x = pyxel.width // 2 - 6  # ドアの中心に合わせた位置
                target_y = self.clear_door_y + 35
                
                # X軸の移動
                if abs(self.pet_x - target_x) > 1:
                    if self.pet_x < target_x:
                        self.pet_x += 1
                    elif self.pet_x > target_x:
                        self.pet_x -= 1
                else:
                    self.pet_x = target_x  # 完全に中心に合わせる
                
                # 位置が合ったらY軸方向に移動開始
                if abs(self.pet_x - target_x) <= 1:
                    if self.pet_y > target_y:
                        self.pet_y -= 1
                    
                    # 目標位置に到達したら閉扉開始
                    if self.pet_y <= target_y:
                        self.door_state = 4
                        self.clear_timer = 0
            
            # ドアの閉扉（より自然な動き）
            elif self.door_state == 4:
                if self.door_open_width > 0:
                    self.door_open_width = max(0, self.door_open_width - 0.5)
                if self.door_open_width <= 0:
                    self.door_state = 5
                    self.clear_timer = 0
            
            # クリア画面への遷移
            elif self.door_state == 5 and self.clear_timer > 30:
                self.show_clear_screen = True
            
            return
        
        # 昼夜サイクルの更新（速度を昼夜で変える）
        if self.is_darkening:
            self.day_cycle += self.day_speed
            if self.day_cycle >= 0.5:  # 0.5で夜になったら明け始める
                self.is_darkening = False
                self.day_cycle = 0.5  # 夜の開始値で固定
                # 夜になった時点で新しい夜明けの速度を設定
                self.night_speed = pyxel.rndf(0.001, 0.005)
        else:
            self.day_cycle += self.night_speed  # 夜明けは速く
            if self.day_cycle >= 0.6:
                self.is_darkening = True
                self.day_cycle = 0  # 最小値で固定
                # 昼になった時点で新しい夜への速度を設定
                self.day_speed = pyxel.rndf(0.001, 0.005)
        
        # 便意ゲージの増加（徐々に速くなる）
        self.poop_speed_multiplier += self.poop_acceleration
        self.poop_gauge += self.base_poop_increase * self.poop_speed_multiplier
        
        # 回復効果の増加
        self.heal_multiplier += self.heal_acceleration
        
        if self.speed < self.max_speed:
            self.speed += self.speed_increase
        
        # スピードに応じて生成間隔を調整
        spawn_interval = int(30 / self.speed)
        spawn_interval = max(10, spawn_interval)
        
        if pyxel.frame_count % spawn_interval == 0:
            # 各レーンでスペースをチェックし、空いているレーンのリストを作成
            available_lanes = []
            for lane in range(3):
                if self.is_space_clear(self.lane_centers[lane], 0):
                    available_lanes.append(lane)
            
            # 空いているレーンがある場合、1つのレーンにのみ生成
            if available_lanes:
                # ランダムに空いているレーンを1つ選択
                lane = available_lanes[pyxel.rndi(0, len(available_lanes) - 1)]
                # 障害物、ゴミ袋、アイテムをランダムに1つ生成
                if pyxel.rndi(0, 20) >= 1:
                    if pyxel.rndi(0, 1) == 0:
                        self.obstacles.append([self.lane_centers[lane], 0])
                    else:
                        self.trash_bags.append([self.lane_centers[lane], 0])
                else:
                    if pyxel.rndi(0,1) == 0:
                        self.power_items.append([self.lane_centers[lane] + 2, 0])
                    else:
                        self.flashlight_items.append([self.lane_centers[lane] + 2, 0])
        
        # シフトキーが押されているかチェック
        if pyxel.btn(pyxel.KEY_SHIFT) and self.stamina_gauge > 0:
            self.stamina_gauge -= 1
        elif self.stamina_gauge < 100:
            self.stamina_gauge += 0.2
        current_speed = self.pet_speed_fast if (pyxel.btn(pyxel.KEY_SHIFT) and self.stamina_gauge > 0)else self.pet_speed

        # 左右キーで移動速度を設定（現在の速度を使用）
        if pyxel.btn(pyxel.KEY_LEFT):
            self.pet_vx = -current_speed
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.pet_vx = current_speed
        
        self.pet_x += self.pet_vx
        
        if self.pet_x < self.left_wall:
            self.pet_x = self.left_wall
            self.pet_vx = -self.pet_vx
        if self.pet_x > self.right_wall:
            self.pet_x = self.right_wall
            self.pet_vx = -self.pet_vx

        for obstacle in self.obstacles:
            obstacle[1] += self.speed
            if obstacle[1] > pyxel.height:
                self.obstacles.remove(obstacle)
            if abs(obstacle[0] - self.pet_x) < 12 and abs(obstacle[1] - self.pet_y) < 12:
                self.game_over = True
                self.game_over_reason = "Look ahead!!"
        
        for trash_bag in self.trash_bags:
            trash_bag[1] += self.speed
            if trash_bag[1] > pyxel.height:
                self.trash_bags.remove(trash_bag)
            if abs(trash_bag[0] - self.pet_x) < 12 and abs(trash_bag[1] - self.pet_y) < 12:
                # 回復量に倍率を用
                heal_amount = self.base_heal_amount * self.heal_multiplier
                self.poop_gauge = max(self.poop_gauge - heal_amount, 0)
                self.trash_bags.remove(trash_bag)
        
        for item in self.power_items:
            item[1] += self.speed
            if item[1] > pyxel.height:
                self.power_items.remove(item)
            if abs(item[0] - self.pet_x) < 12 and abs(item[1] - self.pet_y) < 12:
                self.has_power = True
                self.power_timer = self.power_duration
                self.power_items.remove(item)

        for light in self.flashlight_items:
            light[1] += self.speed
            if light[1] > pyxel.height:
                self.flashlight_items.remove(light)
            if abs(light[0] - self.pet_x) < 12 and abs(light[1] - self.pet_y) < 12:
                self.has_flashlight = True
                self.fl_timer = self.flashlight_duration
                self.flashlight_items.remove(light)
        
        if self.poop_gauge >= 100:
            self.game_over = True
            self.game_over_reason = "Don't leave the poop behind!!"

        # スコアを更新（時間経過で増加）
        self.score += self.speed * 0.1
        # パワーアップ効果の更新
        if self.has_power:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.has_power = False
        # 懐中電灯の効果時間更新
        if self.has_flashlight:
            self.fl_timer -= 1
        if self.fl_timer <= 0:
            self.has_flashlight = False
        
        # リロードタイマーの更新
        if self.reload_timer > 0:
            self.reload_timer -= 1
        
        # 弾の発射
        if self.has_power and pyxel.btnp(pyxel.KEY_SPACE) and self.reload_timer == 0:
            # 犬の上方向に弾を発射
            self.bullets.append([
                self.pet_x + 3,   # 犬の中心より少し左から発射（大きくなった弾の中心調整）
                self.pet_y,       # 犬の上端から発射
                0,                # X方向の速度
                -4                # Y方向の速度
            ])
            self.reload_timer = self.reload_time
        
        # 弾の移動と当たり判定
        for bullet in self.bullets[:]:
            # 弾の移動（Y方向のみ）
            bullet[1] += bullet[3]  # Y座標の更新
            
            # 画面外に出たら削除
            if bullet[1] < -10:  # 上端判定に変更
                self.bullets.remove(bullet)
                continue
            
            # 障害物との当たり判定
            for obstacle in self.obstacles[:]:
                if (abs(bullet[0] - obstacle[0]) < 12 and
                    abs(bullet[1] - obstacle[1]) < 12):
                    self.obstacles.remove(obstacle)
                    self.bullets.remove(bullet)
                    break

        # 進行度の更新（時間経過で少しずつ進む）
        self.progress += 0.5
        
        # クリア判定
        if self.progress >= self.max_progress:
            self.is_cleared = True

    def draw(self):
        if not self.game_started:
            # スタート画面の描画
            pyxel.cls(3)  # 明るい緑の背景
            
            # タイトルテキスト
            pyxel.text(60, 40, "Sampo Game", 7)
            pyxel.text(48, 70, "PRESS S TO START", 7)
            
            # 回転する犬のアニメーション
            center_x = pyxel.width // 2
            center_y = 55
            rotation = self.title_pet_rotation
            
            # とがった耳（常に表示）
            # 左耳
            pyxel.tri(
                center_x - 7, center_y - 2,  # 耳の付け根左
                center_x - 4, center_y - 2,  # 耳の付け根右
                center_x - 5, center_y - 8,  # 耳の先端
                4  # 茶色
            )
            # 右耳
            pyxel.tri(
                center_x + 4, center_y - 2,  # 耳の付け根左
                center_x + 7, center_y - 2,  # 耳の付け根右
                center_x + 5, center_y - 8,  # 耳の先端
                4  # 茶色
            )
            
            # 回転に応じて犬の見た目を変更
            if rotation < 8:  # 正面
                # 通常の犬
                pyxel.circ(center_x, center_y, 6, 4)
                pyxel.pset(center_x - 2, center_y - 2, 0)  # 左目
                pyxel.pset(center_x + 2, center_y - 2, 0)  # 右目
                pyxel.pset(center_x, center_y + 1, 0)      # 鼻
            elif rotation < 16:  # 右向き
                pyxel.circ(center_x, center_y, 6, 4)
                pyxel.pset(center_x + 3, center_y - 2, 0)  # 目
                pyxel.pset(center_x + 4, center_y, 0)      # 鼻
            elif rotation < 24:  # 後ろ
                pyxel.circ(center_x, center_y, 6, 4)
            else:  # 左向き
                pyxel.circ(center_x, center_y, 6, 4)
                pyxel.pset(center_x - 3, center_y - 2, 0)  # 目
                pyxel.pset(center_x - 4, center_y, 0)      # 鼻
            
            return
        
        if self.game_over:
            pyxel.cls(0)  # 画面を黒く暗転
            pyxel.text(65, 50, "GAME OVER", 8)
            if self.poop_gauge >= 100:
                pyxel.text(25, 60,"Don't leave the poop behind!",7)
            else:
                pyxel.text(60,60,"Look Ahead!",7)
            progress_percent = int((self.progress / self.max_progress) * 100)
            pyxel.text(55, 70, f"Progress: {progress_percent}%", 7)
            pyxel.text(45, 80, "PRESS R TO RESTART", 7)
            return
        
        if self.show_clear_screen:
            # クリア画面の描画
            pyxel.cls(3)
            
            # "GAME CLEAR!" の文字を虹色に点滅
            clear_color = (pyxel.frame_count // 4) % 15 + 1
            pyxel.text(60, 40, "GAME CLEAR!", clear_color)
            for poop in self.poop_list:
                poop_x, poop_y, poop_size = poop
            
            
                # うんちの描画（サイズは便意ゲージに応じて変化）
                # base_size = int(6 * poop_size) + 2  # 最小2、最大8
                
                bounce = math.sin(pyxel.frame_count * 0.2) * 2
                y_offset = bounce
                layers = [
                    {"size": poop_size, "y": 0},
                    {"size": poop_size * 0.85, "y": -poop_size * 0.4},
                    {"size": poop_size * 0.7, "y": -poop_size * 0.8},
                    {"size": poop_size * 0.5, "y": -poop_size * 1.1}
                ]
            
            # 層を描画
                for layer in layers:
                # メインカラー（茶色）
                    pyxel.circ(poop_x, poop_y + layer["y"] + y_offset, layer["size"], 4)
                
                # 左側の影（暗い茶色）
                    shadow_size = layer["size"] * 0.6
                    pyxel.circ(poop_x - layer["size"] * 0.3,poop_y + layer["y"] + y_offset,shadow_size, 2)
                
                # 右側のハイライト（明るい茶色）
                    highlight_size = layer["size"] * 0.4
                    pyxel.circ(poop_x + layer["size"] * 0.3,poop_y + layer["y"] + y_offset,highlight_size, 9)
            
            # トップの装飾（渦巻き効果）
                top_y = poop_y - poop_size * 1.1 + y_offset
                spiral_size = poop_size * 0.3
                pyxel.circ(poop_x, top_y, spiral_size, 4)
                pyxel.circ(poop_x + spiral_size * 0.5, 
                        top_y - spiral_size * 0.5,
                        spiral_size * 0.7,4)
            # リスタート案内
            pyxel.text(45, 70, "PRESS R TO RESTART", 7)
            return
        
        # 背景色の計算（3:明るい緑、1:暗い緑）
        bg_color = 3 if self.day_cycle < 0.5 else 1
        
        # 背景を描画
        pyxel.cls(bg_color)
        
        # レーンの色も昼夜で変更（11:明るい緑、9:暗い緑）
        lane_color = 10 if bg_color == 3 else 0
        
        # レーンを区切る線
        pyxel.rect(0, 0, 2, 120, lane_color)    # 左端の線
        pyxel.rect(20, 0, 2, 120, lane_color)   # 左から1番目の線
        pyxel.rect(60, 0, 2, 120, lane_color)   # 左から2番目の線
        pyxel.rect(100, 0, 2, 120, lane_color)  # 左から3番目の線
        pyxel.rect(140, 0, 2, 120, lane_color)  # 左から4番目の線
        pyxel.rect(158, 0, 2, 120, lane_color)  # 右端の線
        
        # 犬の描画
        dog_color = 4  # 茶色
        nose_color = 0  # 黒
        
        # 基準位置
        x = self.pet_x
        y = self.pet_y
        width = 12
        height = 12  # 正方形に変更
        
        # 体（四角形）- より大きな正方形に
        # pyxel.rect(x, y, width, height, dog_color)
        
        # 目（2つの点）
        pyxel.pset(x + width//2 - 2, y + height//3, nose_color)  # 左目
        pyxel.pset(x + width//2 + 2, y + height//3, nose_color)  # 右目
        
        # 鼻（点）
        nose_y = y + height//2
        pyxel.pset(x + width//2, nose_y, nose_color)
        
        # 昼間または夜明け中のみ障害物、ゴミ袋、アイテムを表示
        # is_visible = bg_color == 3  # 背景が明るい時のみ表示

        is_visible = bg_color == 3
        
        if is_visible or self.has_flashlight == True:
            # 障害物（クリスマスツリー風の木）
            for obstacle in self.obstacles:
                x = obstacle[0]
                y = obstacle[1]
                
                # 葉（緑の三角形）- より大きく
                pyxel.tri(
                    x + 6, y - 4,      # 頂点（上に伸ばす）
                    x - 2, y + 12,     # 左下（左に広げる）
                    x + 14, y + 12,    # 右下（右に広げる）
                    11                  # 暗い緑
                )
                
                # 内側の三角（明るい緑）- より大きく
                pyxel.tri(
                    x + 6, y,          # 頂点
                    x + 1, y + 10,     # 左下
                    x + 11, y + 10,    # 右下
                    11                 # 明るい緑
                )
                
                # 幹（茶色の長方形）- 細長く調整
                trunk_width = 4  # 幅を細く
                trunk_height = 8  # 高さを高く
                trunk_x = x + 5  # 中心に配置
                trunk_y = y + 13  # 少し下に移動
                pyxel.rect(trunk_x, trunk_y, trunk_width, trunk_height, 4)
            
            # ゴミ袋（丸みのあるデザイン）
            for trash_bag in self.trash_bags:
                x = trash_bag[0]
                y = trash_bag[1]
                size = 12
                
                # メインの袋部分（楕円形）
                pyxel.circ(x + size//2, y + size//2, size//2, 6)  # 基本形（薄い灰色）
                
                # 上部の結び目（小さな楕円）
                pyxel.circ(x + size//2, y + 2, 2, 7)  # 白色
                
                # 影の表現（より暗い部分）
                pyxel.circb(x + size//2, y + size//2, size//2 - 1, 5)  # 輪郭（濃い灰色）
                
                # 光の反射（ハイライト）
                pyxel.pset(x + size//2 - 2, y + size//2 - 2, 7)  # 白い点

            for item in self.power_items:
                x = item[0]
                y = item[1]
                size = 12
                
                # メインの袋部分（楕円形）
                pyxel.circ(x + size//2, y + size//2, 4, 10)  # 黄色い星
                pyxel.circb(x + size //2, y + size//2, 4, 7)  # 白い縁取り

            for light in self.flashlight_items:
                x = light[0]
                y = light[1]
                size = 12
                
                # メインの袋部分（楕円形）
                pyxel.rect(x - 3, y - 2, 6, 4, 7)  # 本体
                pyxel.rect(x + 3, y - 1, 2, 2, 10) # 電球部分
                pyxel.circb(x + 4, y, 3, 10)    # 白い縁取り
        
        
        # 便意ゲージのラベル位置を上に移動）
        # pyxel.text(5, 5, "Poop Meter", 7)
        pyxel.text(5, 25, "Stamina", 7)
        
        # # 便意ゲージの描画（位置を下に移動）
        # poop_gauge_width = 100
        # poop_gauge_height = 8
        # poop_gauge_y = 15  # ゲージのY座標を調整

        stamina_gauge_width = 100
        stamina_gauge_height = 8
        stamina_gauge_y = 35
        
        # # ゲージの背景（）
        # pyxel.rect(5, poop_gauge_y, poop_gauge_width, poop_gauge_height, 7)
        pyxel.rect(5, stamina_gauge_y, stamina_gauge_width, stamina_gauge_height, 7)
        
        # # ゲージの中身
        # current_width = int((self.poop_gauge * poop_gauge_width) / 100)
        # poop_gauge_color = 9 if self.poop_gauge < 70 else 8
        # pyxel.rect(5, poop_gauge_y, current_width, poop_gauge_height, poop_gauge_color)

        current_width = int((self.stamina_gauge * stamina_gauge_width) / 100)
        stamina_gauge_color = 9 if self.stamina_gauge < 70 else 8
        pyxel.rect(5, stamina_gauge_y, current_width, stamina_gauge_height, stamina_gauge_color)
             
        # # スコアを右上に表示（整数で表示）
        # score_text = f"Score: {int(self.score)}"
        # score_x = pyxel.width - len(score_text) * 4 - 5
        # pyxel.text(score_x, 5, score_text, 7)

        # 夜が近づいてきた時の警告表示
        if self.is_darkening and 0.4 <= self.day_cycle < 0.5 and not self.is_cleared:
            warning_text = "Night approaching"
            text_width = len(warning_text) * 4
            x = (pyxel.width - text_width) // 2
            y = 60  # 画面中央より少し上
            # 滅効果（30フレームごとに切り替え）
            if (pyxel.frame_count // 30) % 2 == 0:
                pyxel.text(x, y, warning_text, 8)  # 赤色で表
        
        # 弾の描画
        for bullet in self.bullets:
            # 大きな弾
            pyxel.rect(bullet[0], bullet[1], 8, 12, 8)
            pyxel.rect(bullet[0] + 1, bullet[1] + 1, 6, 10, 14)
        
        # 犬の描画（パワーアップ中は点滅）
        dog_color = 4  # 通常の茶色
        if self.has_power and not self.is_cleared:
            if (pyxel.frame_count % 8) < 4:
                dog_color = 10  # 金色（黄色）
        
        # とがった耳の描画
        # 左耳
        pyxel.tri(
            self.pet_x + 1, self.pet_y + 4,     # 耳の付け根左
            self.pet_x + 4, self.pet_y + 4,     # 耳の付け根右
            self.pet_x + 2, self.pet_y - 2,     # 耳の先端
            dog_color
        )
        # 右耳
        pyxel.tri(
            self.pet_x + 8, self.pet_y + 4,     # 耳の付け根左
            self.pet_x + 11, self.pet_y + 4,    # 耳の付け根右
            self.pet_x + 10, self.pet_y - 2,    # 耳の先端
            dog_color
        )
        pyxel.tri(
            self.pet_x - 1, self.pet_y + height//2,     # 右
            self.pet_x - 4, self.pet_y + height//2 - 2, # 上
            self.pet_x - 4, self.pet_y + height//2 + 2, # 下
            dog_color
        )
        
        # 犬の本体
        pyxel.circ(self.pet_x + 6, self.pet_y + 6, 6, dog_color)
        
        # 懐中電灯の光を表現（効果中のみ）
        if self.has_flashlight and self.is_cleared == False:
            pyxel.tri(
                self.pet_x + 6,     self.pet_y - 2,  # 下部中央
                self.pet_x + 3,     self.pet_y - 6,  # 左上
                self.pet_x + 9,     self.pet_y - 6,  # 右上
                10  # 黄色
            )
        
        # 目と鼻
        pyxel.pset(self.pet_x + 6 - 2, self.pet_y + 6 - 2, 0)  # 左目
        pyxel.pset(self.pet_x + 6 + 2, self.pet_y + 6 - 2, 0)  # 右目
        pyxel.pset(self.pet_x + 6, self.pet_y + 6 + 1, 0)      # 鼻

        # 進行度ゲージの描画（より右端に）
        gauge_x = pyxel.width - 20  # 160 - 20 = 140
        gauge_y = 15
        gauge_height = 80
        
        # ゲージの背景
        pyxel.rect(gauge_x - 2, gauge_y - 2, 14, gauge_height + 4, 7)  # 白い縁取り
        pyxel.rect(gauge_x, gauge_y, 10, gauge_height, 1)  # 暗い背景
        
        # 進行度に応じたゲージの描画
        progress_height = int((self.progress * gauge_height) / self.max_progress)
        pyxel.rect(gauge_x, gauge_y + gauge_height - progress_height, 
                   10, progress_height, 11)  # 水色でゲージを表示
        
        # 家のアイコン（ゴり右に）
        house_x = gauge_x - 2
        house_y = gauge_y - 15
        
        # 屋根（茶色）
        pyxel.tri(house_x, house_y + 8, 
                  house_x + 7, house_y, 
                  house_x + 14, house_y + 8, 4)
        
        # 本体（白）
        pyxel.rect(house_x + 2, house_y + 8, 10, 10, 7)
        
        # ドア（茶色）
        pyxel.rect(house_x + 6, house_y + 12, 3, 6, 4)
        # ドアノブ（黄色）
        pyxel.pset(house_x + 7, house_y + 15, 10)

        # 便意ゲージとうんちオブジェクトの描画
        gauge_x = 5
        gauge_y = 5
        
        pyxel.text(gauge_x, gauge_y, "Poop Meter", 7)
        pyxel.rect(gauge_x, gauge_y + 10, 100, 8, 7)
        pyxel.rect(gauge_x, gauge_y + 10, self.poop_gauge, 8, 14)
        
        # うんちオブジェクトのアニメーション
        if self.poop_gauge > 0:
            poop_x = gauge_x + self.poop_gauge  # ゲージに合わせて位置を変更
            poop_y = gauge_y + 14
            
            # うんちの大きさをゲージに応じて変更
            size_factor = self.poop_gauge / 100.0  # 0.0 から 1.0 の値
            
            # うんちの描画（サイズは便意ゲージに応じて変化）
            base_size = int(6 * size_factor) + 2  # 最小2、最大8
            
            if self.poop_gauge > 80:
                bounce = math.sin(pyxel.frame_count * 0.2) * 2
                y_offset = bounce
            else:
                y_offset = 0
            layers = [
                {"size": base_size, "y": 0},
                {"size": base_size * 0.85, "y": -base_size * 0.4},
                {"size": base_size * 0.7, "y": -base_size * 0.8},
                {"size": base_size * 0.5, "y": -base_size * 1.1}
            ]
        
        # 層を描画
            for layer in layers:
            # メインカラー（茶色）
                pyxel.circ(poop_x, poop_y + layer["y"] + y_offset, layer["size"], 4)
            
            # 左側の影（暗い茶色）
                shadow_size = layer["size"] * 0.6
                pyxel.circ(poop_x - layer["size"] * 0.3,poop_y + layer["y"] + y_offset,shadow_size, 2)
            
            # 右側のハイライト（明るい茶色）
                highlight_size = layer["size"] * 0.4
                pyxel.circ(poop_x + layer["size"] * 0.3,poop_y + layer["y"] + y_offset,highlight_size, 9)
        
        # トップの装飾（渦巻き効果）
            top_y = poop_y - base_size * 1.1 + y_offset
            spiral_size = base_size * 0.3
            pyxel.circ(poop_x, top_y, spiral_size, 4)
            pyxel.circ(poop_x + spiral_size * 0.5, 
                    top_y - spiral_size * 0.5,
                    spiral_size * 0.7,4)

        # クリアアニメーションの描画
        if self.is_cleared:
            door_x = pyxel.width // 2 - 15
            
            # 犬の描画（ドアが完全に開いているときのみ、かつ閉まり始める前まで）
            if (self.door_state == 3 and 
                self.pet_y > self.clear_door_y + 20):
                # ... existing dog drawing code ...
                pass
            
            # ドアの描画（常に犬の前面）
            if self.door_state < 2 or (self.door_state >= 4 and self.door_open_width == 0):
                # 完全に閉じたドア（開く前と閉じた後で同じ見た目）
                pyxel.rect(door_x, self.clear_door_y, 30, 50, 7)
                pyxel.rectb(door_x, self.clear_door_y, 30, 50, 5)
                pyxel.rect(door_x + 25, self.clear_door_y + 25, 3, 3, 10)
                
            else:  # 開いているときと閉じかけのとき
                # 左扉
                pyxel.rect(door_x - self.door_open_width, self.clear_door_y, 
                          15, 50, 7)
                pyxel.rectb(door_x - self.door_open_width, self.clear_door_y, 
                           15, 50, 5)
                # 左ドアノブ
                pyxel.rect(door_x - self.door_open_width + 12, self.clear_door_y + 25, 
                          3, 3, 10)
                
                # 右扉
                pyxel.rect(door_x + 15 + self.door_open_width, self.clear_door_y, 
                          15, 50, 7)
                pyxel.rectb(door_x + 15 + self.door_open_width, self.clear_door_y, 
                           15, 50, 5)
                # 右ドアノブ
                pyxel.rect(door_x + 15 + self.door_open_width, self.clear_door_y + 25, 
                          3, 3, 10)

    def reset_game(self):
        # Reset all game variables to initial values
        self.pet_x = 80
        self.pet_y = 100
        self.pet_vx = 2.0
        self.poop_gauge = 0
        self.stamina_gauge = 100
        self.obstacles = []
        self.trash_bags = []
        self.speed = 1.0
        self.game_over = False
        self.game_over_reason = ""
        self.score = 0  # スコアもリセット
        self.poop_speed_multiplier = 1.0  # 倍率もリセット
        self.heal_multiplier = 1.0  # 回復効果の倍率もリセット
        self.day_cycle = 0
        self.is_darkening = True
        self.power_items = []
        self.item_spawn_timer = 0
        self.has_power = False
        self.power_timer = 0
        self.bullets = []
        self.reload_timer = 0
        self.flashlight_items = []
        self.fl_timer = 0
        self.has_flashlight = False
        self.progress = 0
        self.is_cleared = False
        self.game_started = False
        self.title_pet_rotation = 0
        self.clear_door_y = -50
        self.door_state = 0
        self.door_open_width = 0
        self.clear_timer = 0
        self.show_clear_screen = False
        self.poop_list = []

WalkGame()