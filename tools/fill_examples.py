"""Fill missing example sentences for CET-4/6 words"""
import json
from pathlib import Path

EXAMPLES = {
    'donkey': "The donkey carried heavy loads up the mountain. 驴子驮着重物上山。",
    'ratio': "The ratio of boys to girls in the class is 2:1. 班上男生与女生的比例是2:1。",
    'microcomputer': "The microcomputer revolutionized personal computing. 微型计算机革命性地改变了个人计算。",
    'France': "France is known for its rich culture and cuisine. 法国以其丰富的文化和美食闻名。",
    'ox': "The ox pulled the plow through the field. 牛拉着犁穿过田地。",
    'butcher': "The butcher cut the meat with precision. 屠夫精准地切肉。",
    'Negro': "The term 'Negro' is now considered outdated and offensive. 'Negro'一词现在被认为过时且具有冒犯性。",
    'China': "China has a long history of civilization. 中国有着悠久的文明历史。",
    'fifty': "There are fifty students in the lecture hall. 演讲厅里有五十名学生。",
    'England': "England is part of the United Kingdom. 英格兰是联合王国的一部分。",
    'fruitful': "The discussion was fruitful and productive. 这次讨论富有成效且多产。",
    'datum': "The datum was recorded accurately in the experiment. 实验中的数据被准确记录。",
    'sofa': "She sat on the sofa reading a book. 她坐在沙发上看书。",
    'printer': "The printer ran out of ink halfway through. 打印机中途没墨了。",
    'narration': "His narration of the story captivated the audience. 他对故事的叙述吸引了观众。",
    'tape': "He used tape to fix the broken book. 他用胶带修补了破损的书。",
    'stern': "The teacher gave him a stern warning. 老师给了他严厉的警告。",
    'Venus': "Venus is the brightest planet in the night sky. 金星是夜空中最亮的行星。",
    'mast': "The flag was raised to the top of the mast. 旗帜被升到了桅杆顶部。",
    'hull': "The hull of the ship was painted blue. 船体被漆成了蓝色。",
    'purify': "This filter can purify the water. 这个过滤器可以净化水。",
    'treasurer': "The treasurer reported the annual budget. 财务主管汇报了年度预算。",
    'buffalo': "The buffalo roamed freely across the plains. 野牛在平原上自由漫步。",
    'wrestle': "The two athletes began to wrestle. 两名运动员开始摔跤。",
    'pantry': "She stocked the pantry with food for the winter. 她在食品储藏室里备好了过冬的食物。",
    'graphite': "Graphite is used in pencil leads. 石墨用于制造铅笔芯。",
    'ohm': "The resistor has a value of 100 ohms. 这个电阻的阻值是100欧姆。",
    'waitress': "The waitress brought us the menu. 女服务员给我们拿来了菜单。",
    'module': "Each module of the course lasts six weeks. 课程的每个模块持续六周。",
    'destine': "They were destined to meet again. 他们注定会再次相遇。",
    'brightness': "The brightness of the sun hurt his eyes. 太阳的光芒刺痛了他的眼睛。",
    'reed': "The reed swayed gently in the wind. 芦苇在风中轻轻摇曳。",
    'bridle': "She put a bridle on the horse. 她给马套上了缰绳。",
    'flux': "The magnetic flux was measured carefully. 磁通量被仔细测量。",
    'allied': "The allied forces worked together during the war. 盟军在战争期间协同作战。",
    'ion': "An ion is an atom with an electric charge. 离子是带有电荷的原子。",
    'whale': "The whale surfaced to breathe. 鲸鱼浮出水面呼吸。",
    'firmness': "He spoke with firmness and confidence. 他说话坚定而自信。",
    'glider': "The glider soared silently above the hills. 滑翔机在山丘上空无声地翱翔。",
    'granite': "The countertop is made of polished granite. 台面由抛光花岗岩制成。",
    'correlate': "The results correlate with the earlier findings. 这些结果与早先的发现相关。",
    'hurrah': "The crowd shouted hurrah as the team won. 球队获胜时人群欢呼喝彩。",
    'boiler': "The boiler heats water for the building. 锅炉为整栋建筑供热。",
    'valuable': "This painting is extremely valuable. 这幅画极其珍贵。",
    'coffin': "The coffin was placed in the grave. 棺材被放入墓穴中。",
    'energize': "A good breakfast will energize you for the day. 一顿好的早餐会让你一天精力充沛。",
    'installment': "He paid the loan in monthly installments. 他按月分期偿还贷款。",
    'propagation': "The propagation of sound waves depends on the medium. 声波的传播依赖于介质。",
    'orient': "The course is designed to orient new students. 这门课程旨在帮助新生适应环境。",
    'capacitance': "Capacitance is measured in farads. 电容以法拉为单位测量。",
    'burner': "Turn off the gas burner after cooking. 做完饭后关掉煤气灶。",
    'gorilla': "The gorilla beat its chest in display of strength. 大猩猩捶胸展示力量。",
    'vocabulary': "Reading widely helps expand your vocabulary. 广泛阅读有助于扩大词汇量。",
    'herald': "The robin is a herald of spring. 知更鸟是春天的预兆。",
    'lathe': "The worker operated the lathe to shape the metal. 工人操作车床来 shaping 金属。",
    'tactics': "The general discussed battle tactics with his officers. 将军与军官们讨论战术。",
    'panther': "The panther moved silently through the jungle. 黑豹在丛林中无声地穿行。",
    'lily': "The lily bloomed in the garden. 百合花在花园里盛开了。",
    'blond': "She has long blond hair and blue eyes. 她有着金色的长发和蓝色的眼睛。",
    'dwarf': "The dwarf star is much smaller than the sun. 矮星比太阳小得多。",
    'shuttle': "The shuttle bus runs between the hotel and the airport. 摆渡车在酒店和机场之间运行。",
    'Moslem': "Moslem refers to a follower of Islam. 穆斯林指的是伊斯兰教的信徒。",
}

def main():
    words_file = Path(__file__).parent.parent / "data" / "words.json"
    with open(words_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 全部转小写匹配
    examples_lower = {k.lower(): v for k, v in EXAMPLES.items()}
    filled = 0
    for cat in ('cet4', 'cet6'):
        for w in data.get(cat, []):
            word = w['word'].lower()
            if not w.get('example', '').strip() and word in examples_lower:
                w['example'] = examples_lower[word]
                filled += 1
                print(f"  {cat}: {w['word']}")
    
    with open(words_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nFilled {filled} words with examples")

if __name__ == '__main__':
    main()
