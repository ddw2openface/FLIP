import torch
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
from data.fs2ksde_dataset import fs2ksde_train, fs2ksde_test
from data.coco_karpathy_dataset import coco_karpathy_train, coco_karpathy_caption_eval, coco_karpathy_retrieval_eval
from data.celeba_dataset import celeba_train, celeba_test
from data.celeba_caption_dataset import celeba_caption_train, celeba_caption_test
from data.facecaption_dataset import facecaption_train, facecaption_test
from data.randaugment import RandomAugment
from data.celeba_dialog_dataset import celeba_dialog_train, celeba_dialog_test
from data.lfwa_dataset import lfwa_train, lfwa_test

def create_dataset(dataset, config, min_scale=0.5):
    
    normalize = transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))

    transform_train = transforms.Compose([
            transforms.Resize((config['image_size'], config['image_size']),interpolation=InterpolationMode.BICUBIC),
            transforms.RandomHorizontalFlip(),
            RandomAugment(2,5,isPIL=True,augs=['Identity','Brightness','Sharpness','Equalize',
                                              'ShearX', 'ShearY', 'TranslateX', 'TranslateY', 'Rotate']),
            transforms.ToTensor(),
            normalize,
        ])
    transform_test = transforms.Compose([
        transforms.Resize((config['image_size'], config['image_size']),interpolation=InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        normalize,
        ])  
        
    if dataset=='coco':          
        train_dataset = coco_karpathy_train(transform_train, config['image_root'], config['ann_root'])
        val_dataset = coco_karpathy_retrieval_eval(transform_test, config['image_root'], config['ann_root'], 'val') 
        # test_dataset = coco_karpathy_retrieval_eval(transform_test, config['image_root'], config['ann_root'], 'test')          
        return train_dataset, val_dataset#, test_dataset
    
    elif dataset=='celeba':          
        train_dataset = celeba_train(transform_train, config['image_root'], config['csv_root'])
        test_dataset = celeba_test(transform_test, config['image_root'], config['csv_root'])       
        return train_dataset, test_dataset
    
    elif dataset=='lfwa':
        train_dataset = lfwa_train(transform_train, config['image_root'], config['csv_root'])
        test_dataset = lfwa_test(transform_test, config['image_root'], config['csv_root'])
        return test_dataset,test_dataset
        
    elif dataset=='celebacaption':       
        train_dataset = celeba_caption_train(transform_train, config['image_root'], config['ann_root'])
        test_dataset = celeba_caption_test(transform_test, config['image_root'], config['ann_root'], 'test')
        return train_dataset, test_dataset#, val_dataset
    
    elif dataset=='fs2ksde':
        train_dataset = fs2ksde_train(transform_train, config['image_root'], config['ann_root'])
        test_dataset = fs2ksde_test(transform_test, config['image_root'], config['ann_root'], 'test')             
        return train_dataset, test_dataset
    
    elif dataset=='facecaption':
        train_dataset = facecaption_train(transform_train, config['image_root'], config['ann_root'])
        # test_dataset = facecaption_test(transform_test, config['image_root'], config['ann_root'])
        eval_dataset = celeba_caption_test(transform_test, config['celeba_image_root'], config['celeba_ann_root'], 'test')
        return train_dataset, eval_dataset
    
    elif dataset=='celebadialog':       
        train_dataset = celeba_dialog_train(transform_train, config['image_root'], config['ann_root'])
        test_dataset = celeba_dialog_test(transform_test, config['image_root'], config['ann_root'], 'test')
        return train_dataset, test_dataset#, val_dataset
    
    
def create_sampler(datasets, shuffles, num_tasks, global_rank):
    samplers = []
    for dataset,shuffle in zip(datasets,shuffles):
        sampler = torch.utils.data.DistributedSampler(dataset, num_replicas=num_tasks, rank=global_rank, shuffle=shuffle)
        samplers.append(sampler)
    return samplers     


def create_loader(datasets, samplers, batch_size, num_workers, is_trains, collate_fns):
    loaders = []
    for dataset,sampler,bs,n_worker,is_train,collate_fn in zip(datasets,samplers,batch_size,num_workers,is_trains,collate_fns):
        if is_train:
            shuffle = (sampler is None)
            drop_last = True
        else:
            shuffle = False
            drop_last = False
        loader = DataLoader(
            dataset,
            batch_size=bs,
            num_workers=n_worker,
            pin_memory=True,
            sampler=sampler,
            shuffle=shuffle,
            collate_fn=collate_fn,
            drop_last=drop_last,
        )              
        loaders.append(loader)
    return loaders    

